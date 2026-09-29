"""Fail-closed validation that citations map to retrieved passages."""

from __future__ import annotations

import re
from dataclasses import dataclass

from app.assistant.outputs import Citation, GroundedAnswer
from app.assistant.registry import RetrievedPassageRegistry


@dataclass(frozen=True)
class GroundingError(Exception):
    reason: str

    def __str__(self) -> str:
        return self.reason


# Filings and model output often disagree on quote glyphs; treat them as the same.
_QUOTE_TRANSLATION = str.maketrans(
    {
        "\u2018": "'",
        "\u2019": "'",
        "\u201c": '"',
        "\u201d": '"',
        "\u00a0": " ",
    }
)


def _normalize_text(text: str) -> str:
    flattened = text.translate(_QUOTE_TRANSLATION)
    return re.sub(r"\s+", " ", flattened.strip())


class GroundingValidator:
    def validate(
        self,
        answer: GroundedAnswer,
        registry: RetrievedPassageRegistry,
    ) -> None:
        if answer.insufficient_evidence:
            if answer.citations:
                raise GroundingError(
                    "insufficient_evidence answers must not include citations"
                )
            return

        if not answer.citations:
            raise GroundingError("grounded answers must include at least one citation")

        seen_indices: set[int] = set()
        for citation in answer.citations:
            self._validate_citation(citation, registry, seen_indices)

    def _validate_citation(
        self,
        citation: Citation,
        registry: RetrievedPassageRegistry,
        seen_indices: set[int],
    ) -> None:
        if citation.citation_index in seen_indices:
            raise GroundingError(
                f"duplicate citation_index {citation.citation_index}"
            )
        seen_indices.add(citation.citation_index)

        passage = registry.get(citation.chunk_id)
        if passage is None:
            raise GroundingError(
                f"citation references chunk {citation.chunk_id} that was not retrieved"
            )

        excerpt = _normalize_text(citation.excerpt)
        if not excerpt:
            raise GroundingError("citation excerpt must not be empty")

        passage_text = _normalize_text(passage.text)
        if excerpt not in passage_text:
            raise GroundingError(
                f"citation excerpt for index {citation.citation_index} "
                "is not a verbatim substring of the retrieved passage"
            )
