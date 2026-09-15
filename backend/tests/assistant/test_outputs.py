from uuid import UUID

import pytest
from pydantic import ValidationError

from app.assistant.outputs import Citation, GroundedAnswer


def test_grounded_answer_requires_citations_when_not_insufficient() -> None:
    with pytest.raises(ValidationError, match="at least one citation"):
        GroundedAnswer(answer="No citations here.", citations=[])


def test_grounded_answer_rejects_citations_with_insufficient_evidence() -> None:
    with pytest.raises(ValidationError, match="insufficient_evidence"):
        GroundedAnswer(
            answer="Missing evidence.",
            insufficient_evidence=True,
            citations=[
                Citation(
                    chunk_id=UUID(int=1),
                    citation_index=0,
                    excerpt="text",
                )
            ],
        )
