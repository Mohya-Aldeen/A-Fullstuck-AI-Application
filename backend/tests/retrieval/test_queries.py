import asyncio
from dataclasses import dataclass
from uuid import UUID

from app.retrieval.models import SearchFilters
from app.retrieval.queries import (
    get_surrounding_chunks,
    hydrate_chunks,
    lexical_search,
    semantic_search,
)


@dataclass
class FakeResponse:
    data: object


class FakeRPCQuery:
    def __init__(self, data: object) -> None:
        self.data = data

    async def execute(self) -> FakeResponse:
        return FakeResponse(self.data)


class FakeTableQuery:
    def __init__(self, client: "FakeClient", table: str) -> None:
        self.client = client
        self.table = table
        self.operations: list[tuple] = []

    def select(self, columns: str):
        self.operations.append(("select", columns))
        return self

    def in_(self, column: str, values: list[str]):
        self.operations.append(("in", column, values))
        return self

    def eq(self, column: str, value):
        self.operations.append(("eq", column, value))
        return self

    def lt(self, column: str, value):
        self.operations.append(("lt", column, value))
        return self

    def gt(self, column: str, value):
        self.operations.append(("gt", column, value))
        return self

    def order(self, column: str, *, desc: bool = False):
        self.operations.append(("order", column, desc))
        return self

    def limit(self, count: int):
        self.operations.append(("limit", count))
        return self

    async def execute(self) -> FakeResponse:
        self.client.table_calls.append(self)
        return FakeResponse(self.client.table_responses.pop(0))


class FakeClient:
    def __init__(self) -> None:
        self.rpc_calls: list[tuple[str, dict]] = []
        self.rpc_responses: dict[str, object] = {}
        self.table_calls: list[FakeTableQuery] = []
        self.table_responses: list[object] = []

    def rpc(self, name: str, params: dict) -> FakeRPCQuery:
        self.rpc_calls.append((name, params))
        return FakeRPCQuery(self.rpc_responses[name])

    def table(self, name: str) -> FakeTableQuery:
        return FakeTableQuery(self, name)


def chunk_row(chunk_id: UUID, document_id: UUID, chunk_index: int) -> dict:
    return {
        "id": str(chunk_id),
        "document_id": str(document_id),
        "chunk_index": chunk_index,
        "text": f"chunk {chunk_index}",
        "token_count": 10,
        "page_label": str(chunk_index),
        "section_label": "Item 7",
        "chunk_metadata": {"ticker": "AAPL"},
        "filing": {
            "id": str(document_id),
            "ticker": "AAPL",
            "company_name": "Apple Inc.",
            "filing_type": "10-K",
            "filing_date": "2021-10-29",
            "filing_year": 2021,
            "accession_number": "0000320193-21-000105",
            "source_url": "https://www.sec.gov/example",
        },
    }


def test_search_rpcs_receive_filters_and_parse_ranked_ids() -> None:
    client = FakeClient()
    semantic_id = UUID(int=1)
    lexical_id = UUID(int=2)
    client.rpc_responses = {
        "match_document_chunks": [{"chunk_id": str(semantic_id), "score": 0.91}],
        "search_document_chunks": [{"chunk_id": str(lexical_id), "score": 0.42}],
    }
    filters = SearchFilters(
        tickers=("AAPL",),
        filing_types=("10-K",),
        start_year=2021,
        end_year=2025,
    )

    semantic = asyncio.run(
        semantic_search(
            client,
            [0.1, 0.2],
            candidate_count=50,
            filters=filters,
        )
    )
    lexical = asyncio.run(
        lexical_search(
            client,
            "Apple revenue",
            candidate_count=50,
            filters=filters,
        )
    )

    assert semantic[0].chunk_id == semantic_id
    assert lexical[0].chunk_id == lexical_id
    assert client.rpc_calls[0] == (
        "match_document_chunks",
        {
            "query_embedding": [0.1, 0.2],
            "match_count": 50,
            "filter_tickers": ["AAPL"],
            "filter_filing_types": ["10-K"],
            "filter_start_year": 2021,
            "filter_end_year": 2025,
        },
    )
    assert client.rpc_calls[1][1]["search_query"] == "Apple revenue"


def test_hydration_restores_fused_id_order() -> None:
    client = FakeClient()
    document_id = UUID(int=10)
    first = UUID(int=1)
    second = UUID(int=2)
    client.table_responses = [
        [
            chunk_row(second, document_id, 8),
            chunk_row(first, document_id, 3),
        ]
    ]

    chunks = asyncio.run(hydrate_chunks(client, [first, second]))

    assert [chunk.chunk_id for chunk in chunks] == [first, second]
    assert chunks[0].filing is not None
    assert chunks[0].filing.ticker == "AAPL"
    assert ("in", "id", [str(first), str(second)]) in client.table_calls[0].operations


def test_surrounding_chunks_use_ordered_queries_not_index_arithmetic() -> None:
    client = FakeClient()
    document_id = UUID(int=10)
    anchor_id = UUID(int=2)
    client.table_responses = [
        [chunk_row(anchor_id, document_id, 7)],
        [chunk_row(UUID(int=1), document_id, 3)],
        [chunk_row(UUID(int=3), document_id, 20)],
    ]

    chunks = asyncio.run(get_surrounding_chunks(client, anchor_id, before=1, after=1))

    assert [chunk.chunk_index for chunk in chunks] == [3, 7, 20]
    assert ("lt", "chunk_index", 7) in client.table_calls[1].operations
    assert ("gt", "chunk_index", 7) in client.table_calls[2].operations
    assert (
        "eq",
        "document_id",
        str(document_id),
    ) in client.table_calls[2].operations
