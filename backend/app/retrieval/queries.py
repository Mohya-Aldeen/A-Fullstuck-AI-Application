"""Supabase RPC and chunk-read queries for hybrid retrieval."""

from __future__ import annotations

from datetime import date
from uuid import UUID

from supabase import AsyncClient

from app.retrieval.models import (
    ChunkRecord,
    FilingMetadata,
    RankedChunk,
    SearchFilters,
)

_CHUNKS = "document_chunks"
_SEMANTIC_RPC = "match_document_chunks"
_LEXICAL_RPC = "search_document_chunks"
_CHUNK_WITH_FILING = (
    "id,document_id,chunk_index,text,token_count,page_label,section_label,"
    "chunk_metadata,"
    "filing:source_documents!inner("
    "id,ticker,company_name,filing_type,filing_date,filing_year,"
    "accession_number,source_url"
    ")"
)


def _response_rows(data: object, *, operation: str) -> list[dict]:
    if data is None:
        return []
    if not isinstance(data, list) or not all(isinstance(row, dict) for row in data):
        raise RuntimeError(f"Unexpected Supabase response for {operation}")
    return data


def _ranked_chunks(data: object, *, operation: str) -> list[RankedChunk]:
    return [
        RankedChunk(chunk_id=UUID(row["chunk_id"]), score=float(row["score"]))
        for row in _response_rows(data, operation=operation)
    ]


def _chunk_from_row(row: dict) -> ChunkRecord:
    filing_row = row.get("filing")
    if not isinstance(filing_row, dict):
        raise TypeError("Chunk response is missing joined filing metadata")
    document_id = UUID(row["document_id"])
    filing = FilingMetadata(
        document_id=UUID(filing_row["id"]),
        ticker=str(filing_row["ticker"]),
        company_name=str(filing_row["company_name"]),
        filing_type=str(filing_row["filing_type"]),
        filing_date=date.fromisoformat(str(filing_row["filing_date"])[:10]),
        filing_year=int(filing_row["filing_year"]),
        accession_number=str(filing_row["accession_number"]),
        source_url=str(filing_row["source_url"]),
    )
    if filing.document_id != document_id:
        raise RuntimeError("Chunk and joined filing document IDs do not match")
    metadata = row.get("chunk_metadata")
    return ChunkRecord(
        chunk_id=UUID(row["id"]),
        document_id=document_id,
        chunk_index=int(row["chunk_index"]),
        text=str(row["text"]),
        token_count=int(row["token_count"]),
        page_label=row.get("page_label"),
        section_label=row.get("section_label"),
        chunk_metadata=metadata if isinstance(metadata, dict) else {},
        filing=filing,
    )


async def semantic_search(
    client: AsyncClient,
    query_embedding: list[float],
    *,
    candidate_count: int,
    filters: SearchFilters,
) -> list[RankedChunk]:
    params = {
        "query_embedding": query_embedding,
        "match_count": candidate_count,
        **filters.rpc_params(),
    }
    response = await client.rpc(_SEMANTIC_RPC, params).execute()
    return _ranked_chunks(response.data, operation=_SEMANTIC_RPC)


async def lexical_search(
    client: AsyncClient,
    query: str,
    *,
    candidate_count: int,
    filters: SearchFilters,
) -> list[RankedChunk]:
    params = {
        "search_query": query,
        "match_count": candidate_count,
        **filters.rpc_params(),
    }
    response = await client.rpc(_LEXICAL_RPC, params).execute()
    return _ranked_chunks(response.data, operation=_LEXICAL_RPC)


async def hydrate_chunks(
    client: AsyncClient,
    chunk_ids: list[UUID],
) -> list[ChunkRecord]:
    if not chunk_ids:
        return []
    response = await (
        client.table(_CHUNKS)
        .select(_CHUNK_WITH_FILING)
        .in_("id", [str(chunk_id) for chunk_id in chunk_ids])
        .execute()
    )
    chunks = [
        _chunk_from_row(row)
        for row in _response_rows(response.data, operation="hydrate chunks")
    ]
    by_id = {chunk.chunk_id: chunk for chunk in chunks}
    missing = [chunk_id for chunk_id in chunk_ids if chunk_id not in by_id]
    if missing:
        raise RuntimeError(f"Could not hydrate {len(missing)} retrieved chunk(s)")
    return [by_id[chunk_id] for chunk_id in chunk_ids]


async def get_chunk(client: AsyncClient, chunk_id: UUID) -> ChunkRecord | None:
    response = await (
        client.table(_CHUNKS)
        .select(_CHUNK_WITH_FILING)
        .eq("id", str(chunk_id))
        .limit(1)
        .execute()
    )
    rows = _response_rows(response.data, operation="read chunk")
    return _chunk_from_row(rows[0]) if rows else None


async def get_surrounding_chunks(
    client: AsyncClient,
    chunk_id: UUID,
    *,
    before: int,
    after: int,
) -> list[ChunkRecord]:
    anchor = await get_chunk(client, chunk_id)
    if anchor is None:
        return []

    previous: list[ChunkRecord] = []
    if before:
        response = await (
            client.table(_CHUNKS)
            .select(_CHUNK_WITH_FILING)
            .eq("document_id", str(anchor.document_id))
            .lt("chunk_index", anchor.chunk_index)
            .order("chunk_index", desc=True)
            .limit(before)
            .execute()
        )
        previous = [
            _chunk_from_row(row)
            for row in _response_rows(response.data, operation="read previous chunks")
        ]
        previous.reverse()

    following: list[ChunkRecord] = []
    if after:
        response = await (
            client.table(_CHUNKS)
            .select(_CHUNK_WITH_FILING)
            .eq("document_id", str(anchor.document_id))
            .gt("chunk_index", anchor.chunk_index)
            .order("chunk_index")
            .limit(after)
            .execute()
        )
        following = [
            _chunk_from_row(row)
            for row in _response_rows(response.data, operation="read following chunks")
        ]

    return [*previous, anchor, *following]
