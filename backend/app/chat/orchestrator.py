"""Coordinates one chat turn: validate, stream, persist."""

from __future__ import annotations

from collections.abc import AsyncIterator
from dataclasses import dataclass
from uuid import UUID, uuid4

from fastapi import HTTPException, status
from pydantic_ai.ui.vercel_ai.request_types import UIMessage
from supabase import AsyncClient

from app.auth.dependencies import CurrentUser, require_thread_owner
from app.chat.messages import (
    STUB_ASSISTANT_REPLY,
    build_assistant_ui_message,
    extract_last_user_message,
    message_text,
    parse_stream_request,
    title_from_first_message,
    ui_message_to_dict,
)
from app.chat.streaming import stream_assistant_text
from app.database import chats as chat_db


@dataclass(frozen=True)
class TurnContext:
    thread_id: UUID
    thread_title: str
    user_message: UIMessage
    user_text: str
    existing_message_count: int
    user_sequence: int
    assistant_message_id: str
    assistant_text: str


async def prepare_turn(
    *,
    user: CurrentUser,
    client: AsyncClient,
    body: dict,
) -> TurnContext:
    try:
        request = parse_stream_request(body)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid chat stream payload: {exc}",
        ) from exc

    thread = await chat_db.get_thread(client, request.thread_id)
    if thread is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Thread not found",
        )
    require_thread_owner(user, thread.user_id)

    user_message = extract_last_user_message(request.messages)
    if user_message is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="At least one user message is required",
        )

    user_text = message_text(user_message)
    if not user_text:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="User message must include text content",
        )

    existing_messages = await chat_db.list_messages(client, request.thread_id)
    user_sequence = await chat_db.next_sequence(client, request.thread_id)

    return TurnContext(
        thread_id=request.thread_id,
        thread_title=thread.title,
        user_message=user_message,
        user_text=user_text,
        existing_message_count=len(existing_messages),
        user_sequence=user_sequence,
        assistant_message_id=str(uuid4()),
        assistant_text=STUB_ASSISTANT_REPLY,
    )


async def run_turn(context: TurnContext, client: AsyncClient) -> AsyncIterator[str]:
    async for event in stream_assistant_text(
        context.assistant_text,
        message_id=context.assistant_message_id,
    ):
        yield event

    await chat_db.append_message(
        client,
        thread_id=context.thread_id,
        role="user",
        ui_message=ui_message_to_dict(context.user_message),
        sequence=context.user_sequence,
    )
    await chat_db.append_message(
        client,
        thread_id=context.thread_id,
        role="assistant",
        ui_message=build_assistant_ui_message(
            text=context.assistant_text,
            message_id=context.assistant_message_id,
        ),
        sequence=context.user_sequence + 1,
        message_id=UUID(context.assistant_message_id),
    )

    if context.existing_message_count == 0 and context.thread_title == "New chat":
        await chat_db.update_thread(
            client,
            context.thread_id,
            title=title_from_first_message(context.user_text),
        )
