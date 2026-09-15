import asyncio
from datetime import date
from uuid import UUID

from app.assistant.registry import RetrievedPassageRegistry
from app.assistant.tools_adapter import InstrumentedRetrievalTools
from app.retrieval.models import ChunkRecord, FilingMetadata, SourcePassage


class FakeRetriever:
    async def search(self, query, *, filters=None, limit=10):
        return [self._passage()]

    async def read_chunk(self, chunk_id):
        return self._passage()

    async def read_surrounding_chunks(self, chunk_id, *, before=1, after=1):
        return [self._passage()]

    def _passage(self) -> SourcePassage:
        document_id = UUID(int=99)
        chunk = ChunkRecord(
            chunk_id=UUID(int=1),
            document_id=document_id,
            chunk_index=0,
            text="Registered passage text.",
            token_count=5,
            page_label="3",
            section_label=None,
            filing=FilingMetadata(
                document_id=document_id,
                ticker="AAPL",
                company_name="Apple Inc.",
                filing_type="10-K",
                filing_date=date(2021, 10, 29),
                filing_year=2021,
                accession_number="acc",
                source_url="https://example.com",
            ),
        )
        from app.retrieval.models import passage_from_chunk

        return passage_from_chunk(chunk)


def test_instrumented_tools_register_passages_on_search() -> None:
    registry = RetrievedPassageRegistry()
    tools = InstrumentedRetrievalTools(retriever=FakeRetriever(), registry=registry)
    passages = asyncio.run(tools.search_filings("revenue"))
    assert len(passages) == 1
    assert registry.get(passages[0].chunk_id) is not None
