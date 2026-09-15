"""Tracks source passages retrieved during one assistant turn."""

from __future__ import annotations

from uuid import UUID

from app.retrieval.models import SourcePassage


class RetrievedPassageRegistry:
    def __init__(self) -> None:
        self._by_chunk_id: dict[UUID, SourcePassage] = {}

    def register(self, passage: SourcePassage) -> None:
        self._by_chunk_id[passage.chunk_id] = passage

    def register_many(self, passages: list[SourcePassage]) -> None:
        for passage in passages:
            self.register(passage)

    def get(self, chunk_id: UUID) -> SourcePassage | None:
        return self._by_chunk_id.get(chunk_id)

    def all_passages(self) -> list[SourcePassage]:
        return list(self._by_chunk_id.values())
