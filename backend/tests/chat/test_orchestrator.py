import asyncio
from uuid import UUID

from pydantic_ai.ui.vercel_ai.request_types import TextUIPart, UIMessage

import app.chat.orchestrator as orchestrator_module
from app.assistant.outputs import Citation, GroundedAnswer
from app.chat.orchestrator import TurnContext, run_turn
from app.database import chats as chat_db


def _user_message(text: str) -> UIMessage:
    return UIMessage(
        id="user-1",
        role="user",
        parts=[TextUIPart(type="text", text=text)],
    )


def test_run_turn_persists_messages_and_citations_on_success(monkeypatch) -> None:
    chunk_id = UUID(int=42)
    grounded = GroundedAnswer(
        answer="Grounded answer [1].",
        citations=[
            Citation(
                chunk_id=chunk_id,
                citation_index=0,
                excerpt="source excerpt",
                page_label="10",
            )
        ],
    )
    appended: dict[str, object] = {"citations": None}

    async def fake_run_document_turn(deps, user_text, *, prior_turns):
        return grounded

    def fake_build_agent_deps(**kwargs):
        class FakeRegistry:
            def get(self, cid):
                return None

        class FakeValidator:
            def validate(self, answer, registry):
                return None

        class FakeDeps:
            registry = FakeRegistry()
            validator = FakeValidator()

        return FakeDeps()

    messages: list[dict] = []

    async def fake_append_message(client, **kwargs):
        messages.append(kwargs)

    async def fake_append_citations(client, *, message_id, citations):
        appended["citations"] = (message_id, citations)

    async def fake_update_thread(*args, **kwargs):
        return None

    monkeypatch.setattr(
        orchestrator_module, "run_document_turn", fake_run_document_turn
    )
    monkeypatch.setattr(
        orchestrator_module, "build_agent_deps", fake_build_agent_deps
    )
    monkeypatch.setattr(chat_db, "append_message", fake_append_message)
    monkeypatch.setattr(chat_db, "append_citations", fake_append_citations)
    monkeypatch.setattr(chat_db, "update_thread", fake_update_thread)

    context = TurnContext(
        user_id=UUID(int=1),
        thread_id=UUID(int=2),
        thread_title="New chat",
        user_message=_user_message("Question?"),
        user_text="Question?",
        prior_turns=[],
        existing_message_count=0,
        user_sequence=0,
        assistant_message_id="00000000-0000-0000-0000-000000000101",
    )

    events = asyncio.run(_collect(run_turn(context, object())))
    assert any("Grounded answer" in event for event in events)
    assert len(messages) == 2
    assert appended["citations"] is not None


def test_run_turn_streams_failure_without_persist_on_grounding_error(
    monkeypatch,
) -> None:
    from app.grounding.validator import GroundingError

    async def fake_run_document_turn(deps, user_text, *, prior_turns):
        raise GroundingError("bad citation")

    monkeypatch.setattr(
        orchestrator_module, "run_document_turn", fake_run_document_turn
    )
    monkeypatch.setattr(
        orchestrator_module,
        "build_agent_deps",
        lambda **kwargs: object(),
    )

    async def fail_append(*args, **kwargs):
        raise AssertionError("should not persist on grounding failure")

    monkeypatch.setattr(chat_db, "append_message", fail_append)

    context = TurnContext(
        user_id=UUID(int=1),
        thread_id=UUID(int=2),
        thread_title="Title",
        user_message=_user_message("Question?"),
        user_text="Question?",
        prior_turns=[],
        existing_message_count=1,
        user_sequence=2,
        assistant_message_id="00000000-0000-0000-0000-000000000102",
    )

    events = asyncio.run(_collect(run_turn(context, object())))
    assert any("Document Copilot" in event for event in events)


async def _collect(stream):
    return [event async for event in stream]
