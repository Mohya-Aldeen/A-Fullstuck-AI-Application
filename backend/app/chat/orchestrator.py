"""Coordinates one chat turn: validate, agent, grounding, stream, persist."""

from __future__ import annotations

import structlog
from collections.abc import AsyncIterator
from dataclasses import dataclass
from uuid import UUID, uuid4

from fastapi import HTTPException, status
from pydantic_ai.ui.vercel_ai.request_types import UIMessage
from supabase import AsyncClient

from app.assistant.agent import run_document_turn
from app.assistant.deps import build_agent_deps
from app.auth.dependencies import CurrentUser, require_thread_owner
from app.chat.messages import (
    build_assistant_ui_message,
    extract_last_user_message,
    message_text,
    parse_stream_request,
    stored_ui_message_text,
    title_from_first_message,
    ui_message_to_dict,
)
from app.chat.streaming import stream_assistant_text
from app.database import chats as chat_db
from app.grounding.validator import GroundingError

log = structlog.get_logger(__name__)

_ASSISTANT_FAILURE_MESSAGE = (
    "Document Copilot could not produce a grounded answer for this question. "
    "Please try rephrasing or narrowing the scope."
)


@dataclass(frozen=True)
class TurnContext:
    user_id: UUID
    thread_id: UUID
    thread_title: str
    user_message: UIMessage
    user_text: str
    prior_turns: list[tuple[str, str]]
    existing_message_count: int
    user_sequence: int
    assistant_message_id: str


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
    prior_turns = [
        (message.role, stored_ui_message_text(message.ui_message))
        for message in existing_messages
        if message.role in ("user", "assistant")
    ]
    user_sequence = await chat_db.next_sequence(client, request.thread_id)

    return TurnContext(
        user_id=user.id,
        thread_id=request.thread_id,
        thread_title=thread.title,
        user_message=user_message,
        user_text=user_text,
        prior_turns=prior_turns,
        existing_message_count=len(existing_messages),
        user_sequence=user_sequence,
        assistant_message_id=str(uuid4()),
    )


async def run_turn(context: TurnContext, client: AsyncClient) -> AsyncIterator[str]:
    deps = build_agent_deps(
        user_id=context.user_id,
        thread_id=context.thread_id,
        supabase=client,
    )

    try:
        grounded = await run_document_turn(
            deps,
            context.user_text,
            prior_turns=context.prior_turns,
        )
        deps.validator.validate(grounded, deps.registry)
    except GroundingError as exc:
        log.warning("grounding_failed", reason=str(exc), thread_id=str(context.thread_id))
        async for event in stream_assistant_text(
            _ASSISTANT_FAILURE_MESSAGE,
            message_id=context.assistant_message_id,
        ):
            yield event
        return
    except Exception as exc:
        log.exception("assistant_turn_failed", thread_id=str(context.thread_id))
        async for event in stream_assistant_text(
            _ASSISTANT_FAILURE_MESSAGE,
            message_id=context.assistant_message_id,
        ):
            yield event
        return

    async for event in stream_assistant_text(
        grounded.answer,
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
            text=grounded.answer,
            message_id=context.assistant_message_id,
        ),
        sequence=context.user_sequence + 1,
        message_id=UUID(context.assistant_message_id),
    )

    if grounded.citations:
        await chat_db.append_citations(
            client,
            message_id=UUID(context.assistant_message_id),
            citations=[
                chat_db.NewCitation(
                    chunk_id=citation.chunk_id,
                    citation_index=citation.citation_index,
                    excerpt=citation.excerpt,
                    page_label=(
                        citation.page_label
                        or (
                            passage.page_label
                            if (passage := deps.registry.get(citation.chunk_id))
                            is not None
                            else None
                        )
                    ),
                )
                for citation in grounded.citations
            ],
        )

    if context.existing_message_count == 0 and context.thread_title == "New chat":
        await chat_db.update_thread(
            client,
            context.thread_id,
            title=title_from_first_message(context.user_text),
        )
