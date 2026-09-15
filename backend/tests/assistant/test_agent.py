import asyncio
from uuid import UUID

import pytest

from app.assistant.agent import run_document_turn
from app.assistant.deps import DocumentAgentDeps
from app.assistant.outputs import Citation, GroundedAnswer
from app.assistant.registry import RetrievedPassageRegistry
from app.assistant.tools_adapter import InstrumentedRetrievalTools
from app.grounding.validator import GroundingValidator


class FakeRetriever:
    async def search(self, *args, **kwargs):
        return []

    async def read_chunk(self, *args, **kwargs):
        return None

    async def read_surrounding_chunks(self, *args, **kwargs):
        return []


def test_run_document_turn_delegates_to_agent(monkeypatch) -> None:
    expected = GroundedAnswer(
        answer="No evidence in corpus.",
        citations=[],
        insufficient_evidence=True,
    )

    async def fake_run(prompt, *, deps, usage_limits):
        assert "Current question:" in prompt
        assert deps.user_id == UUID(int=7)

        class Result:
            output = expected

        return Result()

    monkeypatch.setattr("app.assistant.agent.document_agent.run", fake_run)

    registry = RetrievedPassageRegistry()
    deps = DocumentAgentDeps(
        user_id=UUID(int=7),
        thread_id=UUID(int=8),
        tools=InstrumentedRetrievalTools(retriever=FakeRetriever(), registry=registry),
        registry=registry,
        validator=GroundingValidator(),
    )
    result = asyncio.run(
        run_document_turn(deps, "What is revenue?", prior_turns=[("user", "Hi")])
    )
    assert result == expected
