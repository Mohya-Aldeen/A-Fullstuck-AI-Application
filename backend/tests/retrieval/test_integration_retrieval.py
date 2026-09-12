import asyncio

import pytest
from openai import AsyncOpenAI

from app.config import settings
from app.database.supabase import create_service_role_client
from app.retrieval.models import SearchFilters
from app.retrieval.retriever import DocumentRetriever

pytestmark = pytest.mark.integration


def test_live_hybrid_retrieval_gates() -> None:
    async def run_gates() -> None:
        client = await create_service_role_client()
        retriever = DocumentRetriever(
            client,
            AsyncOpenAI(api_key=settings.OPENAI_API_KEY),
        )

        apple = await retriever.search(
            "What were iPhone net sales and Apple's revenue mix in 2021?",
            filters=SearchFilters(
                tickers=("AAPL",),
                filing_types=("10-K",),
                start_year=2021,
                end_year=2021,
            ),
        )
        assert any(
            "iPhone" in passage.text and "191,973" in passage.text for passage in apple
        )
        apple_context = await retriever.read_surrounding_chunks(apple[0].chunk_id)
        assert apple[0].chunk_id in {passage.chunk_id for passage in apple_context}
        assert all(
            passage.document_id == apple[0].document_id for passage in apple_context
        )
        assert [passage.chunk_index for passage in apple_context] == sorted(
            passage.chunk_index for passage in apple_context
        )

        amazon = await retriever.search(
            "Compare AWS operating income with North America and International",
            filters=SearchFilters(
                tickers=("AMZN",),
                filing_types=("10-K",),
                start_year=2021,
                end_year=2025,
            ),
        )
        assert any(
            "AWS" in passage.text and "operating income" in passage.text.lower()
            for passage in amazon
        )

        nvidia = await retriever.search(
            "Data Center demand drivers customer concentration and supply constraints",
            filters=SearchFilters(
                tickers=("NVDA",),
                filing_types=("10-K",),
                start_year=2021,
                end_year=2025,
            ),
        )
        assert any(
            "supply" in passage.text.lower()
            or "customer concentration" in passage.text.lower()
            for passage in nvidia
        )

        assert all(passage.ticker == "AAPL" for passage in apple)
        assert all(passage.ticker == "AMZN" for passage in amazon)
        assert all(passage.ticker == "NVDA" for passage in nvidia)

    asyncio.run(run_gates())
