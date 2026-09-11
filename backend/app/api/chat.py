from typing import Annotated
from uuid import UUID

import httpx
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from postgrest.exceptions import APIError
from pydantic import BaseModel, Field
from supabase import AsyncClient

from app.auth.dependencies import (
    CurrentUser,
    get_current_user,
    get_user_client,
    require_thread_owner,
)
from app.chat.orchestrator import prepare_turn, run_turn
from app.chat.streaming import VERCEL_AI_STREAM_HEADERS
from app.database import chats as chat_db

SSE_CONTENT_TYPE = "text/event-stream"

router = APIRouter(prefix="/chat", tags=["chat"])


class ThreadResponse(BaseModel):
    id: UUID
    title: str
    created_at: str
    updated_at: str


class CitationResponse(BaseModel):
    id: UUID
    chunk_id: UUID
    citation_index: int
    excerpt: str | None
    page_label: str | None


class MessageResponse(BaseModel):
    id: UUID
    role: str
    ui_message: dict
    sequence: int
    created_at: str
    citations: list[CitationResponse]


class CreateThreadRequest(BaseModel):
    title: str = Field(default="New chat", min_length=1, max_length=200)


def _thread_response(record: chat_db.ChatThreadRecord) -> ThreadResponse:
    return ThreadResponse(
        id=record.id,
        title=record.title,
        created_at=record.created_at.isoformat(),
        updated_at=record.updated_at.isoformat(),
    )


def _message_response(record: chat_db.ChatMessageRecord) -> MessageResponse:
    return MessageResponse(
        id=record.id,
        role=record.role,
        ui_message=record.ui_message,
        sequence=record.sequence,
        created_at=record.created_at.isoformat(),
        citations=[
            CitationResponse(
                id=citation.id,
                chunk_id=citation.chunk_id,
                citation_index=citation.citation_index,
                excerpt=citation.excerpt,
                page_label=citation.page_label,
            )
            for citation in record.citations
        ],
    )


def _database_unavailable() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_502_BAD_GATEWAY,
        detail="Supabase database is unavailable",
    )


@router.get("/threads")
async def list_threads(
    user: Annotated[CurrentUser, Depends(get_current_user)],
    client: Annotated[AsyncClient, Depends(get_user_client)],
) -> list[ThreadResponse]:
    try:
        threads = await chat_db.list_threads(client)
    except (APIError, httpx.RequestError) as exc:
        raise _database_unavailable() from exc
    return [_thread_response(thread) for thread in threads if thread.user_id == user.id]


@router.post("/threads", status_code=status.HTTP_201_CREATED)
async def create_thread(
    body: CreateThreadRequest,
    user: Annotated[CurrentUser, Depends(get_current_user)],
    client: Annotated[AsyncClient, Depends(get_user_client)],
) -> ThreadResponse:
    try:
        thread = await chat_db.create_thread(
            client,
            user_id=user.id,
            email=user.email,
            title=body.title,
        )
    except (APIError, httpx.RequestError) as exc:
        raise _database_unavailable() from exc
    return _thread_response(thread)


@router.get("/threads/{thread_id}/messages")
async def list_thread_messages(
    thread_id: UUID,
    user: Annotated[CurrentUser, Depends(get_current_user)],
    client: Annotated[AsyncClient, Depends(get_user_client)],
) -> list[MessageResponse]:
    try:
        thread = await chat_db.get_thread(client, thread_id)
    except (APIError, httpx.RequestError) as exc:
        raise _database_unavailable() from exc

    if thread is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Thread not found")
    require_thread_owner(user, thread.user_id)

    try:
        messages = await chat_db.list_messages(client, thread_id)
    except (APIError, httpx.RequestError) as exc:
        raise _database_unavailable() from exc

    return [_message_response(message) for message in messages]


@router.post("/stream")
async def stream_chat(
    body: dict,
    user: Annotated[CurrentUser, Depends(get_current_user)],
    client: Annotated[AsyncClient, Depends(get_user_client)],
) -> StreamingResponse:
    try:
        context = await prepare_turn(user=user, client=client, body=body)
    except (APIError, httpx.RequestError) as exc:
        raise _database_unavailable() from exc

    async def event_stream():
        try:
            async for event in run_turn(context, client):
                yield event
        except (APIError, httpx.RequestError) as exc:
            raise _database_unavailable() from exc

    return StreamingResponse(
        event_stream(),
        media_type=SSE_CONTENT_TYPE,
        headers=VERCEL_AI_STREAM_HEADERS,
    )
