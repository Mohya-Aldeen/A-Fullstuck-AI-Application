"""Retrieval tools that register passages for grounding validation."""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from app.assistant.registry import RetrievedPassageRegistry
from app.retrieval.models import SourcePassage
from app.retrieval.retriever import DocumentRetriever
from app.retrieval.tools import RetrievalTools


@dataclass
class InstrumentedRetrievalTools:
    retriever: DocumentRetriever
    registry: RetrievedPassageRegistry

    def __post_init__(self) -> None:
        self._inner = RetrievalTools(self.retriever)

    async def search_filings(
        self,
        query: str,
        *,
        tickers: list[str] | None = None,
        filing_types: list[str] | None = None,
        start_year: int | None = None,
        end_year: int | None = None,
        limit: int = 10,
    ) -> list[SourcePassage]:
        passages = await self._inner.search_filings(
            query,
            tickers=tickers,
            filing_types=filing_types,
            start_year=start_year,
            end_year=end_year,
            limit=limit,
        )
        self.registry.register_many(passages)
        return passages

    async def read_chunk(self, chunk_id: UUID | str) -> SourcePassage | None:
        passage = await self._inner.read_chunk(chunk_id)
        if passage is not None:
            self.registry.register(passage)
        return passage

    async def read_surrounding_chunks(
        self,
        chunk_id: UUID | str,
        *,
        before: int = 1,
        after: int = 1,
    ) -> list[SourcePassage]:
        passages = await self._inner.read_surrounding_chunks(
            chunk_id,
            before=before,
            after=after,
        )
        self.registry.register_many(passages)
        return passages
