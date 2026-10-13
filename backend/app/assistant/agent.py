"""PydanticAI document agent with bounded retrieval tools."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from pydantic_ai import Agent, ModelRetry, RunContext
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openai import OpenAIProvider
from pydantic_ai.usage import UsageLimits

from app.assistant.deps import DocumentAgentDeps
from app.assistant.history import format_prior_turns
from app.assistant.outputs import GroundedAnswer
from app.config import settings
from app.grounding.repair import example_cells, repair_answer
from app.grounding.validator import GroundingError
from app.retrieval.models import SourcePassage
from app.retrieval.tools import MAX_SEARCH_RESULTS, MAX_SURROUNDING_CHUNKS

_INSTRUCTIONS_PATH = Path(__file__).with_name("instructions.md")
_INSTRUCTIONS = _INSTRUCTIONS_PATH.read_text(encoding="utf-8")


def _chat_model() -> OpenAIChatModel:
    configured = settings.OPENAI_CHAT_MODEL.strip()
    model_name = configured.split(":", 1)[-1] if ":" in configured else configured
    return OpenAIChatModel(
        model_name,
        provider=OpenAIProvider(api_key=settings.OPENAI_API_KEY),
    )


def _bounded(value: int, *, low: int, high: int) -> int:
    return min(max(value, low), high)


def _passage_payload(passage: SourcePassage) -> dict[str, Any]:
    return {
        "chunk_id": str(passage.chunk_id),
        "ticker": passage.ticker,
        "company_name": passage.company_name,
        "filing_type": passage.filing_type,
        "filing_year": passage.filing_year,
        "filing_date": passage.filing_date.isoformat(),
        "page_label": passage.page_label,
        "section_label": passage.section_label,
        "text": passage.text,
    }


document_agent = Agent(
    _chat_model(),
    deps_type=DocumentAgentDeps,
    output_type=GroundedAnswer,
    instructions=_INSTRUCTIONS,
    retries=2,
    defer_model_check=True,
)


def enforce_grounding(
    ctx: RunContext[DocumentAgentDeps],
    output: GroundedAnswer,
) -> GroundedAnswer:
    """Ask the model to retry if a citation is not a verbatim retrieved excerpt."""
    repaired = repair_answer(output, ctx.deps.registry)
    try:
        ctx.deps.validator.validate(repaired, ctx.deps.registry)
    except GroundingError as exc:
        samples = example_cells(
            ctx.deps.registry,
            " ".join(citation.excerpt for citation in output.citations),
        )
        sample_hint = ""
        if samples:
            quoted = "; ".join(f'"{sample}"' for sample in samples)
            sample_hint = f" Copy one of these cells exactly: {quoted}."
        raise ModelRetry(
            "Grounding failed: "
            f"{exc}. Copy citation excerpts as a contiguous substring of the "
            "retrieved passage text. Do not use ellipses."
            f"{sample_hint} If the filings do not support the claim, "
            "set insufficient_evidence=true and leave citations empty."
        ) from exc
    return repaired


document_agent.output_validator(enforce_grounding)


@document_agent.tool
async def search_filings(
    ctx: RunContext[DocumentAgentDeps],
    query: str,
    tickers: list[str] | None = None,
    filing_types: list[str] | None = None,
    start_year: int | None = None,
    end_year: int | None = None,
    limit: int = 10,
) -> list[dict[str, Any]]:
    """Hybrid semantic + full-text search over ingested SEC filing chunks."""
    # The model sometimes asks for more hits than the retriever allows. Clamp
    # instead of failing the whole turn.
    limit = _bounded(limit, low=1, high=MAX_SEARCH_RESULTS)
    try:
        passages = await ctx.deps.tools.search_filings(
            query,
            tickers=tickers,
            filing_types=filing_types,
            start_year=start_year,
            end_year=end_year,
            limit=limit,
        )
    except ValueError as exc:
        raise ModelRetry(str(exc)) from exc
    return [_passage_payload(passage) for passage in passages]


@document_agent.tool
async def read_chunk(
    ctx: RunContext[DocumentAgentDeps],
    chunk_id: str,
) -> dict[str, Any] | None:
    """Read one filing chunk by the chunk_id returned from search."""
    try:
        passage = await ctx.deps.tools.read_chunk(chunk_id)
    except ValueError as exc:
        raise ModelRetry(str(exc)) from exc
    return _passage_payload(passage) if passage is not None else None


@document_agent.tool
async def read_surrounding_chunks(
    ctx: RunContext[DocumentAgentDeps],
    chunk_id: str,
    before: int = 1,
    after: int = 1,
) -> list[dict[str, Any]]:
    """Read ordered chunks before and after a chunk in the same filing."""
    before = _bounded(before, low=0, high=MAX_SURROUNDING_CHUNKS)
    after = _bounded(after, low=0, high=MAX_SURROUNDING_CHUNKS)
    try:
        passages = await ctx.deps.tools.read_surrounding_chunks(
            chunk_id,
            before=before,
            after=after,
        )
    except ValueError as exc:
        raise ModelRetry(str(exc)) from exc
    return [_passage_payload(passage) for passage in passages]


async def run_document_turn(
    deps: DocumentAgentDeps,
    user_text: str,
    *,
    prior_turns: list[tuple[str, str]] | None = None,
) -> GroundedAnswer:
    history = format_prior_turns(prior_turns or [])
    prompt = user_text.strip()
    if history:
        prompt = f"{history}\n\nCurrent question:\n{prompt}"

    usage_limits = UsageLimits(
        tool_calls_limit=settings.ASSISTANT_MAX_TOOL_ROUNDS,
    )
    result = await document_agent.run(
        prompt,
        deps=deps,
        usage_limits=usage_limits,
    )
    output = result.output
    if not isinstance(output, GroundedAnswer):
        raise RuntimeError(f"Expected GroundedAnswer, got {type(output)}")
    return output
