"""PydanticAI document agent with bounded retrieval tools."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from pydantic_ai import Agent, RunContext
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openai import OpenAIProvider
from pydantic_ai.usage import UsageLimits

from app.assistant.deps import DocumentAgentDeps
from app.assistant.history import format_prior_turns
from app.assistant.outputs import GroundedAnswer
from app.config import settings
from app.retrieval.models import SourcePassage

_INSTRUCTIONS_PATH = Path(__file__).with_name("instructions.md")
_INSTRUCTIONS = _INSTRUCTIONS_PATH.read_text(encoding="utf-8")


def _chat_model() -> OpenAIChatModel:
    configured = settings.OPENAI_CHAT_MODEL.strip()
    model_name = configured.split(":", 1)[-1] if ":" in configured else configured
    return OpenAIChatModel(
        model_name,
        provider=OpenAIProvider(api_key=settings.OPENAI_API_KEY),
    )


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
    passages = await ctx.deps.tools.search_filings(
        query,
        tickers=tickers,
        filing_types=filing_types,
        start_year=start_year,
        end_year=end_year,
        limit=limit,
    )
    return [_passage_payload(passage) for passage in passages]


@document_agent.tool
async def read_chunk(
    ctx: RunContext[DocumentAgentDeps],
    chunk_id: str,
) -> dict[str, Any] | None:
    """Read one filing chunk by the chunk_id returned from search."""
    passage = await ctx.deps.tools.read_chunk(chunk_id)
    return _passage_payload(passage) if passage is not None else None


@document_agent.tool
async def read_surrounding_chunks(
    ctx: RunContext[DocumentAgentDeps],
    chunk_id: str,
    before: int = 1,
    after: int = 1,
) -> list[dict[str, Any]]:
    """Read ordered chunks before and after a chunk in the same filing."""
    passages = await ctx.deps.tools.read_surrounding_chunks(
        chunk_id,
        before=before,
        after=after,
    )
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
