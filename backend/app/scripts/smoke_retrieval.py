"""Phase 5 retrieval gate — hybrid search against the ingested Supabase corpus.

Run from backend/ (requires OPENAI_API_KEY + ingested chunks with embeddings):

    uv run python -m app.scripts.smoke_retrieval
"""

from __future__ import annotations

import asyncio
import sys
from collections.abc import Callable
from dataclasses import dataclass

from openai import AsyncOpenAI

from app.config import settings
from app.database.supabase import create_service_role_client
from app.retrieval.models import SearchFilters, SourcePassage
from app.retrieval.retriever import DocumentRetriever


@dataclass(frozen=True)
class RetrievalGate:
    name: str
    query: str
    filters: SearchFilters
    check: Callable[[list[SourcePassage]], str | None]
    """Return None if passed, or a short failure reason."""


def _apple_revenue_mix(passages: list[SourcePassage]) -> str | None:
    if not passages:
        return "no passages returned"
    if not any("iPhone" in p.text and "191,973" in p.text for p in passages):
        return "expected iPhone net sales 191,973 in top passages"
    if not all(p.ticker == "AAPL" for p in passages):
        return "expected only AAPL ticker in filtered results"
    return None


def _amazon_aws_profitability(passages: list[SourcePassage]) -> str | None:
    if not passages:
        return "no passages returned"
    if not any(
        "AWS" in p.text and "operating income" in p.text.lower() for p in passages
    ):
        return "expected AWS operating income language in top passages"
    if not all(p.ticker == "AMZN" for p in passages):
        return "expected only AMZN ticker in filtered results"
    return None


def _nvidia_data_center_risks(passages: list[SourcePassage]) -> str | None:
    if not passages:
        return "no passages returned"
    if not any(
        "supply" in p.text.lower() or "customer concentration" in p.text.lower()
        for p in passages
    ):
        return "expected supply or customer concentration language in top passages"
    if not all(p.ticker == "NVDA" for p in passages):
        return "expected only NVDA ticker in filtered results"
    return None


DEFAULT_GATES: tuple[RetrievalGate, ...] = (
    RetrievalGate(
        name="Apple 2021 revenue mix (client-brief Q1)",
        query="What were iPhone net sales and Apple's revenue mix in 2021?",
        filters=SearchFilters(
            tickers=("AAPL",),
            filing_types=("10-K",),
            start_year=2021,
            end_year=2021,
        ),
        check=_apple_revenue_mix,
    ),
    RetrievalGate(
        name="Amazon AWS vs segments (client-brief Q2)",
        query="Compare AWS operating income with North America and International",
        filters=SearchFilters(
            tickers=("AMZN",),
            filing_types=("10-K",),
            start_year=2021,
            end_year=2025,
        ),
        check=_amazon_aws_profitability,
    ),
    RetrievalGate(
        name="NVIDIA Data Center risks (client-brief Q3)",
        query="Data Center demand drivers customer concentration and supply constraints",
        filters=SearchFilters(
            tickers=("NVDA",),
            filing_types=("10-K",),
            start_year=2021,
            end_year=2025,
        ),
        check=_nvidia_data_center_risks,
    ),
)


def _preview_passage(passage: SourcePassage, *, max_chars: int = 160) -> str:
    excerpt = passage.text.replace("\n", " ").strip()
    if len(excerpt) > max_chars:
        excerpt = excerpt[: max_chars - 1] + "…"
    page = passage.page_label or "?"
    section = passage.section_label or "(no section)"
    return f"{passage.ticker} {passage.filing_year} p.{page} — {section}\n  {excerpt!r}"


async def run_retrieval_gates(
    retriever: DocumentRetriever,
    gates: tuple[RetrievalGate, ...] = DEFAULT_GATES,
    *,
    verbose: bool = True,
) -> list[tuple[RetrievalGate, bool, str]]:
    results: list[tuple[RetrievalGate, bool, str]] = []
    for gate in gates:
        passages = await retriever.search(gate.query, filters=gate.filters)
        reason = gate.check(passages)
        passed = reason is None
        detail = reason or f"{len(passages)} passage(s); top hit OK"
        results.append((gate, passed, detail))
        if verbose:
            status = "PASS" if passed else "FAIL"
            print(f"[{status}] {gate.name}", flush=True)
            print(f"  query: {gate.query}", flush=True)
            print(f"  {detail}", flush=True)
            if passages:
                print(_preview_passage(passages[0]), flush=True)
            print(flush=True)

        if passed and gate.name.startswith("Apple"):
            context = await retriever.read_surrounding_chunks(passages[0].chunk_id)
            neighbor_ok = (
                passages[0].chunk_id in {p.chunk_id for p in context}
                and all(p.document_id == passages[0].document_id for p in context)
                and [p.chunk_index for p in context]
                == sorted(p.chunk_index for p in context)
            )
            if not neighbor_ok:
                passed = False
                detail = "neighbor-chunk fetch failed sanity checks"
                results[-1] = (gate, False, detail)
                if verbose:
                    print(f"  {detail}", flush=True)
                    print("[FAIL] Apple neighbor-chunk check", flush=True)

    return results


async def _async_main() -> int:
    if not settings.OPENAI_API_KEY.strip().startswith("sk-"):
        print(
            "Smoke retrieval requires a real OPENAI_API_KEY in backend/.env",
            file=sys.stderr,
        )
        return 1

    client = await create_service_role_client()
    retriever = DocumentRetriever(client, AsyncOpenAI(api_key=settings.OPENAI_API_KEY))
    print("Running Phase 5 retrieval gates against Supabase corpus…\n", flush=True)
    results = await run_retrieval_gates(retriever)
    failed = [gate.name for gate, passed, _ in results if not passed]
    if failed:
        print(f"Retrieval smoke FAILED ({len(failed)} gate(s)):", file=sys.stderr)
        for name in failed:
            print(f"  - {name}", file=sys.stderr)
        return 1

    print(f"Retrieval smoke PASSED ({len(results)} gate(s)).", flush=True)
    return 0


def main() -> int:
    return asyncio.run(_async_main())


if __name__ == "__main__":
    raise SystemExit(main())
