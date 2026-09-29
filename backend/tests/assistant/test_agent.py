import asyncio
from datetime import date
from types import SimpleNamespace
from uuid import UUID

import pytest
from pydantic_ai import ModelRetry

from app.assistant.agent import enforce_grounding, run_document_turn
from app.assistant.deps import DocumentAgentDeps
from app.assistant.outputs import Citation, GroundedAnswer
from app.assistant.registry import RetrievedPassageRegistry
from app.assistant.tools_adapter import InstrumentedRetrievalTools
from app.grounding.validator import GroundingValidator
from app.retrieval.models import SourcePassage


class FakeRetriever:
    async def search(self, *args, **kwargs):
        return []

    async def read_chunk(self, *args, **kwargs):
        return None

    async def read_surrounding_chunks(self, *args, **kwargs):
        return []


def test_run_document_turn_delegates_to_agent(monkeypatch) -> None:
    expected = GroundedAnswer(
        answer="No evidence in corpus.",
        citations=[],
        insufficient_evidence=True,
    )

    async def fake_run(prompt, *, deps, usage_limits):
        assert "Current question:" in prompt
        assert deps.user_id == UUID(int=7)

        class Result:
            output = expected

        return Result()

    monkeypatch.setattr("app.assistant.agent.document_agent.run", fake_run)

    registry = RetrievedPassageRegistry()
    deps = DocumentAgentDeps(
        user_id=UUID(int=7),
        thread_id=UUID(int=8),
        tools=InstrumentedRetrievalTools(retriever=FakeRetriever(), registry=registry),
        registry=registry,
        validator=GroundingValidator(),
    )
    result = asyncio.run(
        run_document_turn(deps, "What is revenue?", prior_turns=[("user", "Hi")])
    )
    assert result == expected


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
        filing_date=date(2021, 10, 29),
        filing_year=2021,
        accession_number="0000320193-21-000105",
        source_url="https://www.sec.gov/example",
    )


def _deps_with_passage(text: str) -> DocumentAgentDeps:
    chunk_id = UUID(int=9)
    registry = RetrievedPassageRegistry()
    registry.register(_passage(chunk_id, text))
    return DocumentAgentDeps(
        user_id=UUID(int=7),
        thread_id=UUID(int=8),
        tools=InstrumentedRetrievalTools(retriever=FakeRetriever(), registry=registry),
        registry=registry,
        validator=GroundingValidator(),
    )


def test_enforce_grounding_retries_when_excerpt_is_not_verbatim() -> None:
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


def test_enforce_grounding_accepts_verbatim_excerpt() -> None:
    text = "Net sales of iPhone were $191,973 million."
    deps = _deps_with_passage(text)
    answer = GroundedAnswer(
        answer="iPhone net sales were $191,973 million [1].",
        citations=[
            Citation(chunk_id=UUID(int=9), citation_index=0, excerpt=text),
        ],
    )
    assert enforce_grounding(SimpleNamespace(deps=deps), answer) is answer
