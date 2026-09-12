"""Typed Supabase helpers for source documents and retrieval chunks."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date, datetime
from uuid import UUID, uuid4

from supabase import AsyncClient

_DOCUMENTS = "source_documents"
_CHUNKS = "document_chunks"


@dataclass(frozen=True)
class SourceDocumentRecord:
    id: UUID
    ticker: str
    company_name: str
    filing_type: str
    filing_date: date
    filing_year: int
    accession_number: str
    source_url: str
    markdown_content: str
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True)
class NewChunk:
    chunk_index: int
    text: str
    token_count: int
    embedding: list[float] | None = None
    page_label: str | None = None
    section_label: str | None = None
    chunk_metadata: dict | None = None
    chunk_id: UUID | None = None


def parse_embedding_vector(value: object) -> list[float] | None:
    """Normalize pgvector values returned by Supabase (list or string)."""
    if value is None:
        return None
    if isinstance(value, list):
        return [float(item) for item in value]
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return None
        if text.startswith("[") and text.endswith("]"):
            parsed = json.loads(text)
            if isinstance(parsed, list):
                return [float(item) for item in parsed]
        parts = text.strip("[]").split(",")
        if parts and parts[0]:
            return [float(part.strip()) for part in parts]
    return None


def embedding_dimensions(value: object) -> int:
    vector = parse_embedding_vector(value)
    return len(vector) if vector is not None else 0


def _parse_dt(value: str) -> datetime:
    return datetime.fromisoformat(value)


def _parse_date(value: str) -> date:
    return date.fromisoformat(value[:10])


def _one_row(rows: list[dict] | None, *, what: str) -> dict:
    if not rows:
        raise RuntimeError(f"Expected one {what} row from Supabase, got none")
    return rows[0]


def _document_from_row(row: dict) -> SourceDocumentRecord:
    return SourceDocumentRecord(
        id=UUID(row["id"]),
        ticker=row["ticker"],
        company_name=row["company_name"],
        filing_type=row["filing_type"],
        filing_date=_parse_date(row["filing_date"]),
        filing_year=int(row["filing_year"]),
        accession_number=row["accession_number"],
        source_url=row["source_url"],
        markdown_content=row["markdown_content"],
        created_at=_parse_dt(row["created_at"]),
        updated_at=_parse_dt(row["updated_at"]),
    )


_DOCUMENT_COLUMNS = (
    "id,ticker,company_name,filing_type,filing_date,filing_year,"
    "accession_number,source_url,markdown_content,created_at,updated_at"
)


async def get_document_by_accession(
    client: AsyncClient, accession_number: str
) -> SourceDocumentRecord | None:
    response = await (
        client.table(_DOCUMENTS)
        .select(_DOCUMENT_COLUMNS)
        .eq("accession_number", accession_number)
        .limit(1)
        .execute()
    )
    rows = response.data or []
    if not rows:
        return None
    return _document_from_row(rows[0])


async def insert_source_document(
    client: AsyncClient,
    *,
    ticker: str,
    company_name: str,
    filing_type: str,
    filing_date: date,
    filing_year: int,
    accession_number: str,
    source_url: str,
    markdown_content: str,
    document_id: UUID | None = None,
) -> SourceDocumentRecord:
    row = {
        "id": str(document_id or uuid4()),
        "ticker": ticker,
        "company_name": company_name,
        "filing_type": filing_type,
        "filing_date": filing_date.isoformat(),
        "filing_year": filing_year,
        "accession_number": accession_number,
        "source_url": source_url,
        "markdown_content": markdown_content,
    }
    response = await (
        client.table(_DOCUMENTS)
        .insert(row)
        .select(_DOCUMENT_COLUMNS)
        .execute()
    )
    return _document_from_row(_one_row(response.data, what="source document"))


async def update_source_document(
    client: AsyncClient,
    document_id: UUID,
    *,
    ticker: str,
    company_name: str,
    filing_type: str,
    filing_date: date,
    filing_year: int,
    source_url: str,
    markdown_content: str,
) -> SourceDocumentRecord:
    payload = {
        "ticker": ticker,
        "company_name": company_name,
        "filing_type": filing_type,
        "filing_date": filing_date.isoformat(),
        "filing_year": filing_year,
        "source_url": source_url,
        "markdown_content": markdown_content,
    }
    response = await (
        client.table(_DOCUMENTS)
        .update(payload)
        .eq("id", str(document_id))
        .select(_DOCUMENT_COLUMNS)
        .execute()
    )
    return _document_from_row(_one_row(response.data, what="source document"))


async def delete_chunks_for_document(client: AsyncClient, document_id: UUID) -> None:
    await client.table(_CHUNKS).delete().eq("document_id", str(document_id)).execute()


async def insert_chunks(
    client: AsyncClient,
    *,
    document_id: UUID,
    chunks: list[NewChunk],
    batch_size: int = 40,
) -> int:
    if not chunks:
        return 0

    inserted = 0
    for start in range(0, len(chunks), batch_size):
        batch = chunks[start : start + batch_size]
        rows = [
            {
                "id": str(chunk.chunk_id or uuid4()),
                "document_id": str(document_id),
                "chunk_index": chunk.chunk_index,
                "page_label": chunk.page_label,
                "section_label": chunk.section_label,
                "text": chunk.text,
                "token_count": chunk.token_count,
                "chunk_metadata": chunk.chunk_metadata or {},
                **(
                    {"embedding": chunk.embedding}
                    if chunk.embedding is not None
                    else {}
                ),
            }
            for chunk in batch
        ]
        await client.table(_CHUNKS).insert(rows).execute()
        inserted += len(rows)
    return inserted


async def count_chunks_for_document(client: AsyncClient, document_id: UUID) -> int:
    response = await (
        client.table(_CHUNKS)
        .select("id", count="exact", head=True)
        .eq("document_id", str(document_id))
        .execute()
    )
    return int(response.count or 0)


async def count_embedded_chunks_for_document(
    client: AsyncClient, document_id: UUID
) -> int:
    response = await (
        client.table(_CHUNKS)
        .select("id", count="exact", head=True)
        .eq("document_id", str(document_id))
        .not_.is_("embedding", "null")
        .execute()
    )
    return int(response.count or 0)


async def count_source_documents(client: AsyncClient) -> int:
    response = await (
        client.table(_DOCUMENTS).select("id", count="exact", head=True).execute()
    )
    return int(response.count or 0)


async def count_chunks(client: AsyncClient) -> int:
    response = await client.table(_CHUNKS).select("id", count="exact", head=True).execute()
    return int(response.count or 0)
