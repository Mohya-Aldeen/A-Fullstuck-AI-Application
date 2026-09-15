"""Hybrid retrieval over SEC filing chunks (semantic + full-text + RRF)."""

from app.retrieval.fusion import DEFAULT_RRF_K, reciprocal_rank_fusion
from app.retrieval.models import (
    ChunkRecord,
    FusedChunk,
    RankedChunk,
    SearchFilters,
    SourcePassage,
    passage_from_chunk,
)
from app.retrieval.queries import (
    get_chunk,
    get_surrounding_chunks,
    hydrate_chunks,
    lexical_search,
    semantic_search,
)
from app.retrieval.retriever import DocumentRetriever
from app.retrieval.tools import RetrievalTools

__all__ = [
    "ChunkRecord",
    "DEFAULT_RRF_K",
    "DocumentRetriever",
    "FusedChunk",
    "RankedChunk",
    "RetrievalTools",
    "SearchFilters",
    "SourcePassage",
    "get_chunk",
    "get_surrounding_chunks",
    "hydrate_chunks",
    "lexical_search",
    "passage_from_chunk",
    "reciprocal_rank_fusion",
    "semantic_search",
]
