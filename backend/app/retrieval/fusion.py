"""Rank-only fusion for semantic and lexical retrieval results."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable, Sequence
from uuid import UUID

from app.retrieval.models import FusedChunk, RankedChunk

DEFAULT_RRF_K = 60


def _unique_ranks(ranking: Iterable[RankedChunk]) -> dict[UUID, int]:
    ranks: dict[UUID, int] = {}
    for rank, hit in enumerate(ranking, start=1):
        ranks.setdefault(hit.chunk_id, rank)
    return ranks


def reciprocal_rank_fusion(
    semantic: Sequence[RankedChunk],
    lexical: Sequence[RankedChunk],
    *,
    k: int = DEFAULT_RRF_K,
    limit: int | None = None,
) -> list[FusedChunk]:
    """Fuse rankings by stable chunk ID without mixing branch score scales."""
    if k < 1:
        raise ValueError("RRF k must be at least 1")
    if limit is not None and limit < 1:
        raise ValueError("Fusion limit must be at least 1")

    semantic_ranks = _unique_ranks(semantic)
    lexical_ranks = _unique_ranks(lexical)
    scores: dict[UUID, float] = defaultdict(float)

    for chunk_id, rank in semantic_ranks.items():
        scores[chunk_id] += 1.0 / (k + rank)
    for chunk_id, rank in lexical_ranks.items():
        scores[chunk_id] += 1.0 / (k + rank)

    fused = [
        FusedChunk(
            chunk_id=chunk_id,
            rrf_score=score,
            semantic_rank=semantic_ranks.get(chunk_id),
            lexical_rank=lexical_ranks.get(chunk_id),
        )
        for chunk_id, score in scores.items()
    ]
    fused.sort(
        key=lambda hit: (
            -hit.rrf_score,
            min(
                rank
                for rank in (hit.semantic_rank, hit.lexical_rank)
                if rank is not None
            ),
            str(hit.chunk_id),
        )
    )
    return fused[:limit]
