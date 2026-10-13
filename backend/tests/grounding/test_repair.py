from datetime import date
from types import SimpleNamespace
from uuid import UUID

import pytest
from pydantic_ai import ModelRetry

from app.assistant.agent import enforce_grounding
from app.assistant.outputs import Citation, GroundedAnswer
from app.assistant.registry import RetrievedPassageRegistry
from app.grounding.repair import repair_answer
from app.grounding.validator import GroundingValidator
from app.retrieval.models import SourcePassage
from tests.assistant.test_agent import _deps_with_passage


def _passage(chunk_id: UUID, text: str) -> SourcePassage:
    return SourcePassage(
        chunk_id=chunk_id,
        document_id=UUID(int=10),
        chunk_index=0,
        text=text,
        token_count=10,
        page_label="12",
        section_label="Item 8",
        ticker="AAPL",
        company_name="Apple Inc.",
        filing_type="10-K",
        filing_date=date(2023, 11, 3),
        filing_year=2023,
        accession_number="0000320193-23-000106",
        source_url="https://www.sec.gov/example",
    )


_TABLE = (
    "iPhone (1), 27 = $. iPhone (1), 28 = 191,973. Mac (1), 1 = . Mac (1), 3 = 29,357."
)


def test_repair_replaces_ellipsis_with_table_cells() -> None:
    chunk_id = UUID(int=1)
    registry = RetrievedPassageRegistry()
    registry.register(_passage(chunk_id, _TABLE))
    answer = GroundedAnswer(
        answer="iPhone and Mac net sales changed [1].",
        citations=[
            Citation(
                chunk_id=chunk_id,
                citation_index=0,
                excerpt="iPhone (1), ... 191,973 ... Mac (1), ... 29,357",
            )
        ],
    )
    repaired = repair_answer(answer, registry)
    excerpt = repaired.citations[0].excerpt
    assert "191,973" in excerpt
    assert "29,357" in excerpt
    assert "..." not in excerpt
    GroundingValidator().validate(repaired, registry)


def test_repair_expands_a_trimmed_sentence_to_the_filing_wording() -> None:
    chunk_id = UUID(int=2)
    text = (
        "The Company retains the commission. "
        "Net sales disaggregated by significant products and services "
        "for 2024, 2023 and 2022 were as follows (in millions):"
    )
    registry = RetrievedPassageRegistry()
    registry.register(_passage(chunk_id, text))
    answer = GroundedAnswer(
        answer="The filing introduces the product table [1].",
        citations=[
            Citation(
                chunk_id=chunk_id,
                citation_index=0,
                excerpt=(
                    "Net sales disaggregated by significant products "
                    "... 2022, 2021 were as follows ..."
                ),
            )
        ],
    )
    repaired = repair_answer(answer, registry)
    excerpt = repaired.citations[0].excerpt
    assert "2024, 2023 and 2022" in excerpt
    assert "2022, 2021" not in excerpt
    GroundingValidator().validate(repaired, registry)


def test_repair_drops_an_ungrounded_citation_and_renumbers() -> None:
    good_id = UUID(int=3)
    bad_id = UUID(int=4)
    registry = RetrievedPassageRegistry()
    registry.register(_passage(good_id, "Net sales of iPhone were $191,973 million."))
    registry.register(_passage(bad_id, "Unrelated risk factor language."))
    answer = GroundedAnswer(
        answer="Supported [1]. Invented [2].",
        citations=[
            Citation(
                chunk_id=good_id,
                citation_index=0,
                excerpt="Net sales of iPhone were $191,973 million.",
            ),
            Citation(
                chunk_id=bad_id,
                citation_index=1,
                excerpt="This sentence is not in the filing.",
            ),
        ],
    )
    repaired = repair_answer(answer, registry)
    assert len(repaired.citations) == 1
    assert repaired.citations[0].citation_index == 0
    assert "[2]" not in repaired.answer
    assert "[1]" in repaired.answer
    GroundingValidator().validate(repaired, registry)


def test_repair_leaves_a_fully_ungrounded_answer_unchanged() -> None:
    chunk_id = UUID(int=5)
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
    assert repair_answer(answer, registry) is answer


def test_enforce_grounding_accepts_shortened_table_excerpt() -> None:
    deps = _deps_with_passage(_TABLE)
    answer = GroundedAnswer(
        answer="iPhone net sales were 191,973 [1].",
        citations=[
            Citation(
                chunk_id=UUID(int=9),
                citation_index=0,
                excerpt="iPhone sales were about 191,973",
            )
        ],
    )
    repaired = enforce_grounding(SimpleNamespace(deps=deps), answer)
    assert "191,973" in repaired.citations[0].excerpt
    assert "..." not in repaired.citations[0].excerpt
    GroundingValidator().validate(repaired, deps.registry)


def test_enforce_grounding_still_retries_a_paraphrase() -> None:
    deps = _deps_with_passage("Exact filing sentence here.")
    answer = GroundedAnswer(
        answer="Claim [1].",
        citations=[
            Citation(
                chunk_id=UUID(int=9),
                citation_index=0,
                excerpt="Paraphrased filing sentence.",
            )
        ],
    )
    with pytest.raises(ModelRetry, match="verbatim"):
        enforce_grounding(SimpleNamespace(deps=deps), answer)
