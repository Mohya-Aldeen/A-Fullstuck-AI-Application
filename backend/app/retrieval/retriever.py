"""Query-to-passage orchestration for hybrid filing retrieval."""

from __future__ import annotations

import asyncio
from uuid import UUID

from openai import AsyncOpenAI
from supabase import AsyncClient

from app.config import settings
from app.retrieval.fusion import DEFAULT_RRF_K, reciprocal_rank_fusion
from app.retrieval.models import SearchFilters, SourcePassage, passage_from_chunk
from app.retrieval.queries import (
    get_chunk,
    get_surrounding_chunks,
    hydrate_chunks,
    lexical_search,
    semantic_search,
)

DEFAULT_CANDIDATE_COUNT = 50
DEFAULT_RESULT_COUNT = 10
MAX_CANDIDATE_COUNT = 100
MAX_RESULT_COUNT = 20
MAX_NEIGHBOR_COUNT = 5


class DocumentRetriever:
    def __init__(
        self,
        client: AsyncClient,
        openai_client: AsyncOpenAI,
        *,
        candidate_count: int = DEFAULT_CANDIDATE_COUNT,
        rrf_k: int = DEFAULT_RRF_K,
    ) -> None:
        if not 1 <= candidate_count <= MAX_CANDIDATE_COUNT:
            raise ValueError(
                f"candidate_count must be between 1 and {MAX_CANDIDATE_COUNT}"
            )
        if rrf_k < 1:
            raise ValueError("rrf_k must be at least 1")
        self._client = client
        self._openai_client = openai_client
        self._candidate_count = candidate_count
        self._rrf_k = rrf_k

    async def _embed_query(self, query: str) -> list[float]:
        response = await self._openai_client.embeddings.create(
            model=settings.OPENAI_EMBEDDING_MODEL,
            input=[query],
            dimensions=settings.OPENAI_EMBEDDING_DIMENSIONS,
        )
        if len(response.data) != 1:
            raise RuntimeError(
                f"Expected one query embedding, got {len(response.data)}"
            )
        embedding = response.data[0].embedding
        if len(embedding) != settings.OPENAI_EMBEDDING_DIMENSIONS:
            raise RuntimeError(
                f"Query embedding has {len(embedding)} dimensions; "
                f"expected {settings.OPENAI_EMBEDDING_DIMENSIONS}"
            )
        return embedding

    async def search(
        self,
        query: str,
        *,
        filters: SearchFilters | None = None,
        limit: int = DEFAULT_RESULT_COUNT,
    ) -> list[SourcePassage]:
        normalized_query = query.strip()
        if not normalized_query:
            raise ValueError("Search query must not be empty")
        if not 1 <= limit <= MAX_RESULT_COUNT:
            raise ValueError(f"limit must be between 1 and {MAX_RESULT_COUNT}")

        active_filters = filters or SearchFilters()
        if (
            active_filters.start_year is not None
            and active_filters.end_year is not None
            and active_filters.start_year > active_filters.end_year
        ):
            raise ValueError("start_year must be less than or equal to end_year")

        query_embedding = await self._embed_query(normalized_query)
        semantic, lexical = await asyncio.gather(
            semantic_search(
                self._client,
                query_embedding,
                candidate_count=self._candidate_count,
                filters=active_filters,
            ),
            lexical_search(
                self._client,
                normalized_query,
                candidate_count=self._candidate_count,
                filters=active_filters,
            ),
        )
        fused = reciprocal_rank_fusion(
            semantic,
            lexical,
            k=self._rrf_k,
            limit=limit,
        )
        chunks = await hydrate_chunks(
            self._client,
            [hit.chunk_id for hit in fused],
        )
        return [
            passage_from_chunk(chunk, fused=hit)
            for chunk, hit in zip(chunks, fused, strict=True)
        ]

    async def read_chunk(self, chunk_id: UUID) -> SourcePassage | None:
        chunk = await get_chunk(self._client, chunk_id)
        return passage_from_chunk(chunk) if chunk is not None else None

    async def read_surrounding_chunks(
        self,
        chunk_id: UUID,
        *,
        before: int = 1,
        after: int = 1,
    ) -> list[SourcePassage]:
        if not 0 <= before <= MAX_NEIGHBOR_COUNT:
            raise ValueError(f"before must be between 0 and {MAX_NEIGHBOR_COUNT}")
        if not 0 <= after <= MAX_NEIGHBOR_COUNT:
            raise ValueError(f"after must be between 0 and {MAX_NEIGHBOR_COUNT}")
        chunks = await get_surrounding_chunks(
            self._client,
            chunk_id,
            before=before,
            after=after,
        )
        return [passage_from_chunk(chunk) for chunk in chunks]
