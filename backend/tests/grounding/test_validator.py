from datetime import date
from uuid import UUID

import pytest

from app.assistant.outputs import Citation, GroundedAnswer
from app.assistant.registry import RetrievedPassageRegistry
from app.grounding.validator import GroundingError, GroundingValidator
from app.retrieval.models import FilingMetadata, SourcePassage


def _passage(chunk_id: UUID, text: str) -> SourcePassage:
    document_id = UUID(int=10)
    return SourcePassage(
        chunk_id=chunk_id,
        document_id=document_id,
        chunk_index=0,
        text=text,
        token_count=10,
        page_label="12",
        section_label="Item 7",
        ticker="AAPL",
        company_name="Apple Inc.",
        filing_type="10-K",
        filing_date=date(2021, 10, 29),
        filing_year=2021,
        accession_number="0000320193-21-000105",
        source_url="https://www.sec.gov/example",
    )


def test_validator_accepts_grounded_answer_with_verbatim_excerpt() -> None:
    chunk_id = UUID(int=1)
    registry = RetrievedPassageRegistry()
    registry.register(_passage(chunk_id, "Net sales of iPhone were $191,973 million."))
    answer = GroundedAnswer(
        answer="iPhone net sales were $191,973 million [1].",
        citations=[
            Citation(
                chunk_id=chunk_id,
                citation_index=0,
                excerpt="Net sales of iPhone were $191,973 million.",
            )
        ],
    )
    GroundingValidator().validate(answer, registry)


def test_validator_accepts_insufficient_evidence_without_citations() -> None:
    answer = GroundedAnswer(
        answer="The corpus does not contain enough evidence to answer.",
        citations=[],
        insufficient_evidence=True,
    )
    GroundingValidator().validate(answer, RetrievedPassageRegistry())


def test_validator_rejects_citation_for_unretrieved_chunk() -> None:
    chunk_id = UUID(int=2)
    answer = GroundedAnswer(
        answer="Claim [1].",
        citations=[
            Citation(chunk_id=chunk_id, citation_index=0, excerpt="some text"),
        ],
    )
    with pytest.raises(GroundingError, match="not retrieved"):
        GroundingValidator().validate(answer, RetrievedPassageRegistry())


def test_validator_treats_curly_quotes_as_straight() -> None:
    chunk_id = UUID(int=31)
    registry = RetrievedPassageRegistry()
    registry.register(_passage(chunk_id, 'The company\u2019s iPhone net sales rose.'))
    answer = GroundedAnswer(
        answer="iPhone net sales rose [1].",
        citations=[
            Citation(
                chunk_id=chunk_id,
                citation_index=0,
                excerpt="The company's iPhone net sales rose.",
            )
        ],
    )
    GroundingValidator().validate(answer, registry)


def test_validator_rejects_non_verbatim_excerpt() -> None:
    chunk_id = UUID(int=3)
    registry = RetrievedPassageRegistry()
    registry.register(_passage(chunk_id, "Exact filing sentence here."))
    answer = GroundedAnswer(
        answer="Claim [1].",
        citations=[
            Citation(
                chunk_id=chunk_id,
                citation_index=0,
                excerpt="Paraphrased filing sentence.",
            )
        ],
    )
    with pytest.raises(GroundingError, match="verbatim"):
        GroundingValidator().validate(answer, registry)


def test_validator_rejects_duplicate_citation_index() -> None:
    chunk_id = UUID(int=4)
    registry = RetrievedPassageRegistry()
    text = "Shared excerpt text for duplicate index test."
    registry.register(_passage(chunk_id, text))
    answer = GroundedAnswer(
        answer="Claim [1][2].",
        citations=[
            Citation(chunk_id=chunk_id, citation_index=0, excerpt=text),
            Citation(chunk_id=chunk_id, citation_index=0, excerpt=text),
        ],
    )
    with pytest.raises(GroundingError, match="duplicate"):
        GroundingValidator().validate(answer, registry)
