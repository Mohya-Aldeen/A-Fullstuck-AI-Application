import asyncio
import json
from uuid import UUID, uuid4

import pytest
from supabase import create_async_client

from app.auth.dependencies import CurrentUser
from app.chat.orchestrator import _ASSISTANT_FAILURE_MESSAGE, prepare_turn, run_turn
from app.config import settings
from app.database import chats as chat_db
from app.database.supabase import create_service_role_client, create_user_client

pytestmark = pytest.mark.integration

_QUESTION = (
    "What was Apple's iPhone net sales in the fiscal 2021 10-K? "
    "Cite the filing passage."
)


def _streamed_text(events: list[str]) -> str:
    parts: list[str] = []
    for event in events:
        for line in event.splitlines():
            if not line.startswith("data: "):
                continue
            payload = line.removeprefix("data: ").strip()
            if not payload.startswith("{"):
                continue
            try:
                body = json.loads(payload)
            except json.JSONDecodeError:
                continue
            if isinstance(body, dict) and body.get("type") == "text-delta":
                delta = body.get("delta")
                if isinstance(delta, str):
                    parts.append(delta)
    return "".join(parts)


def test_live_chat_turn_persists_apple_citation() -> None:
    asyncio.run(_live_chat_turn())


async def _live_chat_turn() -> None:
    admin = await create_service_role_client()
    user_id: str | None = None
    try:
        email = f"chat-integration-{uuid4()}@example.com"
        password = f"Integration-{uuid4()}"
        created = await admin.auth.admin.create_user(
            {
                "email": email,
                "password": password,
                "email_confirm": True,
            }
        )
        assert created.user is not None and created.user.id
        user_id = created.user.id

        anon = await create_async_client(
            settings.SUPABASE_URL,
            settings.SUPABASE_ANON_KEY,
        )
        signed_in = await anon.auth.sign_in_with_password(
            {"email": email, "password": password}
        )
        assert signed_in.session is not None
        client = await create_user_client(signed_in.session.access_token)
        user = CurrentUser(id=UUID(user_id), email=email)

        # One bad excerpt fails the turn closed and persists nothing. Retry so a
        # single non-verbatim citation does not fail the whole live path.
        last_stream = ""
        for _attempt in range(3):
            thread = await chat_db.create_thread(
                client,
                user_id=user.id,
                email=email,
                title="New chat",
            )
            context = await prepare_turn(
                user=user,
                client=client,
                body={
                    "threadId": str(thread.id),
                    "messages": [
                        {
                            "id": "user-1",
                            "role": "user",
                            "parts": [{"type": "text", "text": _QUESTION}],
                        }
                    ],
                },
            )

            events = [event async for event in run_turn(context, client)]
            last_stream = _streamed_text(events)
            if _ASSISTANT_FAILURE_MESSAGE in last_stream:
                continue

            messages = await chat_db.list_messages(client, thread.id)
            assert [message.role for message in messages] == ["user", "assistant"]

            citations = messages[1].citations
            assert citations
            assert any(
                citation.source is not None
                and citation.source.ticker == "AAPL"
                and citation.excerpt is not None
                and "iPhone" in citation.excerpt
                for citation in citations
            )
            return

        raise AssertionError(
            "live turn did not persist a grounded Apple citation. "
            f"Last stream: {last_stream[:500]}"
        )
    finally:
        if user_id is not None:
            await admin.auth.admin.delete_user(user_id)
