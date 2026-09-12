"""Bounded retrieval operations intended for later PydanticAI registration."""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from app.retrieval.models import SearchFilters, SourcePassage
from app.retrieval.retriever import DocumentRetriever

MAX_FILTER_VALUES = 10
MAX_SEARCH_RESULTS = 10
MAX_SURROUNDING_CHUNKS = 2


def _normalize_values(
    values: list[str] | None,
    *,
    label: str,
) -> tuple[str, ...]:
    if not values:
        return ()
    if len(values) > MAX_FILTER_VALUES:
        raise ValueError(f"{label} accepts at most {MAX_FILTER_VALUES} values")
    normalized = tuple(dict.fromkeys(value.strip().upper() for value in values))
    if any(not value for value in normalized):
        raise ValueError(f"{label} values must not be empty")
    return normalized


def _chunk_uuid(chunk_id: UUID | str) -> UUID:
    if isinstance(chunk_id, UUID):
        return chunk_id
    try:
        return UUID(chunk_id)
    except ValueError as exc:
        raise ValueError("chunk_id must be a valid UUID") from exc


@dataclass(frozen=True)
class RetrievalTools:
    """Model-facing facade; Phase 6 supplies this through DocumentAgentDeps."""

    retriever: DocumentRetriever

    async def search_filings(
        self,
        query: str,
        *,
        tickers: list[str] | None = None,
        filing_types: list[str] | None = None,
        start_year: int | None = None,
        end_year: int | None = None,
        limit: int = MAX_SEARCH_RESULTS,
    ) -> list[SourcePassage]:
        """Search filing passages using semantic and full-text retrieval."""
        if not 1 <= limit <= MAX_SEARCH_RESULTS:
            raise ValueError(f"limit must be between 1 and {MAX_SEARCH_RESULTS}")
        filters = SearchFilters(
            tickers=_normalize_values(tickers, label="tickers"),
            filing_types=_normalize_values(filing_types, label="filing_types"),
            start_year=start_year,
            end_year=end_year,
        )
        return await self.retriever.search(query, filters=filters, limit=limit)

    async def read_chunk(self, chunk_id: UUID | str) -> SourcePassage | None:
        """Read one complete filing chunk by the stable ID returned from search."""
        return await self.retriever.read_chunk(_chunk_uuid(chunk_id))

    async def read_surrounding_chunks(
        self,
        chunk_id: UUID | str,
        *,
        before: int = 1,
        after: int = 1,
    ) -> list[SourcePassage]:
        """Read a chunk with a small ordered window from the same filing."""
        if not 0 <= before <= MAX_SURROUNDING_CHUNKS:
            raise ValueError(f"before must be between 0 and {MAX_SURROUNDING_CHUNKS}")
        if not 0 <= after <= MAX_SURROUNDING_CHUNKS:
            raise ValueError(f"after must be between 0 and {MAX_SURROUNDING_CHUNKS}")
        return await self.retriever.read_surrounding_chunks(
            _chunk_uuid(chunk_id),
            before=before,
            after=after,
        )
