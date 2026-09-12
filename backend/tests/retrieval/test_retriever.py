import asyncio
from datetime import date
from types import SimpleNamespace
from uuid import UUID

import pytest

import app.retrieval.retriever as retriever_module
from app.config import settings
from app.retrieval.models import (
    ChunkRecord,
    FilingMetadata,
    RankedChunk,
    SearchFilters,
)
from app.retrieval.retriever import DocumentRetriever


class FakeEmbeddings:
    def __init__(self) -> None:
        self.calls: list[dict] = []

    async def create(self, **kwargs):
        self.calls.append(kwargs)
        return SimpleNamespace(
            data=[
                SimpleNamespace(embedding=[0.0] * settings.OPENAI_EMBEDDING_DIMENSIONS)
            ]
        )


class FakeOpenAI:
    def __init__(self) -> None:
        self.embeddings = FakeEmbeddings()


def chunk(chunk_id: UUID, index: int) -> ChunkRecord:
    document_id = UUID(int=100)
    return ChunkRecord(
        chunk_id=chunk_id,
        document_id=document_id,
        chunk_index=index,
        text=f"passage {index}",
        token_count=12,
        page_label=str(index),
        section_label="Item 7",
        filing=FilingMetadata(
            document_id=document_id,
            ticker="AAPL",
            company_name="Apple Inc.",
            filing_type="10-K",
            filing_date=date(2021, 10, 29),
            filing_year=2021,
            accession_number="0000320193-21-000105",
            source_url="https://www.sec.gov/example",
        ),
    )


def test_search_embeds_once_fuses_branches_and_hydrates_in_rank_order(
    monkeypatch,
) -> None:
    semantic_ids = [UUID(int=1), UUID(int=2)]
    lexical_ids = [UUID(int=3), UUID(int=2)]
    calls: dict[str, object] = {}

    async def fake_semantic(client, embedding, *, candidate_count, filters):
        calls["semantic"] = (client, len(embedding), candidate_count, filters)
        return [
            RankedChunk(chunk_id=semantic_ids[0], score=0.9),
            RankedChunk(chunk_id=semantic_ids[1], score=0.8),
        ]

    async def fake_lexical(client, query, *, candidate_count, filters):
        calls["lexical"] = (client, query, candidate_count, filters)
        return [
            RankedChunk(chunk_id=lexical_ids[0], score=8.0),
            RankedChunk(chunk_id=lexical_ids[1], score=7.0),
        ]

    async def fake_hydrate(client, chunk_ids):
        calls["hydrate"] = (client, chunk_ids)
        return [chunk(chunk_id, index) for index, chunk_id in enumerate(chunk_ids)]

    monkeypatch.setattr(retriever_module, "semantic_search", fake_semantic)
    monkeypatch.setattr(retriever_module, "lexical_search", fake_lexical)
    monkeypatch.setattr(retriever_module, "hydrate_chunks", fake_hydrate)

    db = object()
    openai = FakeOpenAI()
    retriever = DocumentRetriever(db, openai)
    filters = SearchFilters(tickers=("AAPL",), start_year=2021, end_year=2021)
    passages = asyncio.run(
        retriever.search("  Apple revenue mix  ", filters=filters, limit=3)
    )

    assert passages[0].chunk_id == UUID(int=2)
    assert passages[0].semantic_rank == 2
    assert passages[0].lexical_rank == 2
    assert passages[0].ticker == "AAPL"
    assert openai.embeddings.calls == [
        {
            "model": settings.OPENAI_EMBEDDING_MODEL,
            "input": ["Apple revenue mix"],
            "dimensions": settings.OPENAI_EMBEDDING_DIMENSIONS,
        }
    ]
    assert calls["semantic"][2:] == (50, filters)
    assert calls["lexical"][1:] == ("Apple revenue mix", 50, filters)
    assert calls["hydrate"][1][0] == UUID(int=2)


def test_search_validates_query_limit_and_year_range() -> None:
    retriever = DocumentRetriever(object(), FakeOpenAI())
    with pytest.raises(ValueError, match="must not be empty"):
        asyncio.run(retriever.search(" "))
    with pytest.raises(ValueError, match="limit"):
        asyncio.run(retriever.search("query", limit=21))
    with pytest.raises(ValueError, match="start_year"):
        asyncio.run(
            retriever.search(
                "query",
                filters=SearchFilters(start_year=2025, end_year=2021),
            )
        )


def test_constructor_bounds_candidate_count() -> None:
    with pytest.raises(ValueError, match="candidate_count"):
        DocumentRetriever(object(), FakeOpenAI(), candidate_count=101)
