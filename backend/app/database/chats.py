"""Typed Supabase helpers for chat threads, messages, and citations."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID, uuid4

from supabase import AsyncClient

_THREADS = "chat_threads"
_MESSAGES = "chat_messages"
_CITATIONS = "message_citations"
_PROFILES = "profiles"


@dataclass(frozen=True)
class ChatThreadRecord:
    id: UUID
    user_id: UUID
    title: str
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True)
class MessageCitationRecord:
    id: UUID
    message_id: UUID
    chunk_id: UUID
    citation_index: int
    excerpt: str | None
    page_label: str | None


@dataclass(frozen=True)
class ChatMessageRecord:
    id: UUID
    thread_id: UUID
    role: str
    ui_message: dict
    sequence: int
    created_at: datetime
    citations: list[MessageCitationRecord]


def _parse_dt(value: str) -> datetime:
    return datetime.fromisoformat(value)


def _thread_from_row(row: dict) -> ChatThreadRecord:
    return ChatThreadRecord(
        id=UUID(row["id"]),
        user_id=UUID(row["user_id"]),
        title=row["title"],
        created_at=_parse_dt(row["created_at"]),
        updated_at=_parse_dt(row["updated_at"]),
    )


def _citation_from_row(row: dict) -> MessageCitationRecord:
    return MessageCitationRecord(
        id=UUID(row["id"]),
        message_id=UUID(row["message_id"]),
        chunk_id=UUID(row["chunk_id"]),
        citation_index=row["citation_index"],
        excerpt=row.get("excerpt"),
        page_label=row.get("page_label"),
    )


def _message_from_row(row: dict) -> ChatMessageRecord:
    raw_citations = row.get("message_citations") or []
    citations = [_citation_from_row(item) for item in raw_citations]
    citations.sort(key=lambda c: c.citation_index)
    return ChatMessageRecord(
        id=UUID(row["id"]),
        thread_id=UUID(row["thread_id"]),
        role=row["role"],
        ui_message=row["ui_message"],
        sequence=row["sequence"],
        created_at=_parse_dt(row["created_at"]),
        citations=citations,
    )


async def ensure_profile(
    client: AsyncClient,
    *,
    user_id: UUID,
    email: str | None,
) -> None:
    """Create a profile row when missing — required before inserting chat_threads."""
    await (
        client.table(_PROFILES)
        .upsert({"id": str(user_id), "email": email}, on_conflict="id")
        .execute()
    )


async def list_threads(client: AsyncClient) -> list[ChatThreadRecord]:
    response = await (
        client.table(_THREADS)
        .select("id,user_id,title,created_at,updated_at")
        .order("updated_at", desc=True)
        .execute()
    )
    return [_thread_from_row(row) for row in response.data or []]


async def create_thread(
    client: AsyncClient,
    *,
    user_id: UUID,
    email: str | None,
    title: str = "New chat",
) -> ChatThreadRecord:
    await ensure_profile(client, user_id=user_id, email=email)
    response = await (
        client.table(_THREADS)
        .insert({"user_id": str(user_id), "title": title})
        .select("id,user_id,title,created_at,updated_at")
        .single()
        .execute()
    )
    return _thread_from_row(response.data)


async def get_thread(client: AsyncClient, thread_id: UUID) -> ChatThreadRecord | None:
    response = await (
        client.table(_THREADS)
        .select("id,user_id,title,created_at,updated_at")
        .eq("id", str(thread_id))
        .maybe_single()
        .execute()
    )
    if response.data is None:
        return None
    return _thread_from_row(response.data)


async def update_thread(
    client: AsyncClient,
    thread_id: UUID,
    *,
    title: str | None = None,
) -> ChatThreadRecord:
    payload: dict[str, str] = {}
    if title is not None:
        payload["title"] = title
    response = await (
        client.table(_THREADS)
        .update(payload)
        .eq("id", str(thread_id))
        .select("id,user_id,title,created_at,updated_at")
        .single()
        .execute()
    )
    return _thread_from_row(response.data)


async def list_messages(client: AsyncClient, thread_id: UUID) -> list[ChatMessageRecord]:
    response = await (
        client.table(_MESSAGES)
        .select("id,thread_id,role,ui_message,sequence,created_at,message_citations(*)")
        .eq("thread_id", str(thread_id))
        .order("sequence")
        .execute()
    )
    return [_message_from_row(row) for row in response.data or []]


async def next_sequence(client: AsyncClient, thread_id: UUID) -> int:
    response = await (
        client.table(_MESSAGES)
        .select("sequence")
        .eq("thread_id", str(thread_id))
        .order("sequence", desc=True)
        .limit(1)
        .execute()
    )
    rows = response.data or []
    if not rows:
        return 0
    return int(rows[0]["sequence"]) + 1


async def append_message(
    client: AsyncClient,
    *,
    thread_id: UUID,
    role: str,
    ui_message: dict,
    sequence: int,
    message_id: UUID | None = None,
) -> ChatMessageRecord:
    row: dict = {
        "thread_id": str(thread_id),
        "role": role,
        "ui_message": ui_message,
        "sequence": sequence,
    }
    if message_id is not None:
        row["id"] = str(message_id)

    response = await (
        client.table(_MESSAGES)
        .insert(row)
        .select("id,thread_id,role,ui_message,sequence,created_at")
        .single()
        .execute()
    )
    return _message_from_row({**response.data, "message_citations": []})


@dataclass(frozen=True)
class NewCitation:
    chunk_id: UUID
    citation_index: int
    excerpt: str | None = None
    page_label: str | None = None


async def append_citations(
    client: AsyncClient,
    *,
    message_id: UUID,
    citations: list[NewCitation],
) -> list[MessageCitationRecord]:
    if not citations:
        return []

    rows = [
        {
            "id": str(uuid4()),
            "message_id": str(message_id),
            "chunk_id": str(citation.chunk_id),
            "citation_index": citation.citation_index,
            "excerpt": citation.excerpt,
            "page_label": citation.page_label,
        }
        for citation in citations
    ]
    response = await (
        client.table(_CITATIONS)
        .insert(rows)
        .select("id,message_id,chunk_id,citation_index,excerpt,page_label")
        .execute()
    )
    return [_citation_from_row(row) for row in response.data or []]
