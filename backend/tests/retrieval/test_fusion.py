from uuid import UUID

import pytest

from app.retrieval.fusion import reciprocal_rank_fusion
from app.retrieval.models import RankedChunk

IDS = [UUID(int=value) for value in range(1, 7)]


def hit(index: int, score: float = 1.0) -> RankedChunk:
    return RankedChunk(chunk_id=IDS[index], score=score)


def test_overlap_is_boosted_above_single_branch_hits() -> None:
    fused = reciprocal_rank_fusion(
        [hit(0), hit(1), hit(2)],
        [hit(3), hit(1), hit(4)],
    )
    assert fused[0].chunk_id == IDS[1]
    assert fused[0].semantic_rank == 2
    assert fused[0].lexical_rank == 2


def test_disjoint_and_empty_rankings_are_supported() -> None:
    fused = reciprocal_rank_fusion([], [hit(2), hit(3)])
    assert [item.chunk_id for item in fused] == [IDS[2], IDS[3]]
    assert all(item.semantic_rank is None for item in fused)


def test_duplicate_id_in_one_branch_counts_only_once() -> None:
    fused = reciprocal_rank_fusion(
        [hit(0), hit(0), hit(1)],
        [],
    )
    assert [item.chunk_id for item in fused] == [IDS[0], IDS[1]]
    assert fused[1].semantic_rank == 3


def test_equal_scores_use_stable_chunk_id_tie_breaker() -> None:
    fused = reciprocal_rank_fusion([hit(1)], [hit(0)])
    assert [item.chunk_id for item in fused] == [IDS[0], IDS[1]]


def test_limit_and_parameters_are_validated() -> None:
    assert len(reciprocal_rank_fusion([hit(0), hit(1)], [], limit=1)) == 1
    with pytest.raises(ValueError, match="RRF k"):
        reciprocal_rank_fusion([], [], k=0)
    with pytest.raises(ValueError, match="Fusion limit"):
        reciprocal_rank_fusion([], [], limit=0)
