import asyncio
from uuid import UUID

import pytest

from app.retrieval.models import SearchFilters
from app.retrieval.tools import RetrievalTools


class FakeRetriever:
    def __init__(self) -> None:
        self.calls: list[tuple] = []

    async def search(
        self,
        query: str,
        *,
        filters: SearchFilters,
        limit: int,
    ) -> list:
        self.calls.append(("search", query, filters, limit))
        return []

    async def read_chunk(self, chunk_id: UUID):
        self.calls.append(("read_chunk", chunk_id))

    async def read_surrounding_chunks(
        self,
        chunk_id: UUID,
        *,
        before: int,
        after: int,
    ) -> list:
        self.calls.append(("surrounding", chunk_id, before, after))
        return []


def test_search_normalizes_filters_and_delegates() -> None:
    retriever = FakeRetriever()
    tools = RetrievalTools(retriever)

    asyncio.run(
        tools.search_filings(
            "revenue mix",
            tickers=[" aapl ", "AAPL"],
            filing_types=["10-k"],
            start_year=2021,
            end_year=2025,
            limit=5,
        )
    )

    _, query, filters, limit = retriever.calls[0]
    assert query == "revenue mix"
    assert filters == SearchFilters(
        tickers=("AAPL",),
        filing_types=("10-K",),
        start_year=2021,
        end_year=2025,
    )
    assert limit == 5


def test_read_tools_parse_uuid_and_bound_context() -> None:
    retriever = FakeRetriever()
    tools = RetrievalTools(retriever)
    chunk_id = UUID(int=42)

    asyncio.run(tools.read_chunk(str(chunk_id)))
    asyncio.run(tools.read_surrounding_chunks(str(chunk_id), before=2, after=0))

    assert retriever.calls == [
        ("read_chunk", chunk_id),
        ("surrounding", chunk_id, 2, 0),
    ]
    with pytest.raises(ValueError, match="valid UUID"):
        asyncio.run(tools.read_chunk("not-a-uuid"))
    with pytest.raises(ValueError, match="before"):
        asyncio.run(tools.read_surrounding_chunks(chunk_id, before=3))


def test_search_output_and_filter_counts_are_bounded() -> None:
    tools = RetrievalTools(FakeRetriever())
    with pytest.raises(ValueError, match="limit"):
        asyncio.run(tools.search_filings("query", limit=11))
    with pytest.raises(ValueError, match="at most"):
        asyncio.run(
            tools.search_filings(
                "query",
                tickers=[f"TICKER{index}" for index in range(11)],
            )
        )
