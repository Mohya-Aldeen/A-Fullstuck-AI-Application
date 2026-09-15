"""Structured assistant output for grounded filing answers."""

from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, Field, model_validator


class Citation(BaseModel):
    chunk_id: UUID
    citation_index: int = Field(ge=0)
    excerpt: str = Field(min_length=1)
    page_label: str | None = None


class GroundedAnswer(BaseModel):
    answer: str = Field(min_length=1)
    citations: list[Citation] = Field(default_factory=list)
    insufficient_evidence: bool = False

    @model_validator(mode="after")
    def _evidence_mode(self) -> GroundedAnswer:
        if self.insufficient_evidence and self.citations:
            raise ValueError(
                "citations must be empty when insufficient_evidence is true"
            )
        if not self.insufficient_evidence and not self.citations:
            raise ValueError(
                "at least one citation is required unless insufficient_evidence is true"
            )
        return self
