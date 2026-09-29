# Phase 6 — LLM assistant and grounding

## Purpose

Write an answer an analyst can trust. Trust here means:

- every factual claim is tied to a retrieved passage
- the passage can be opened and checked
- if the filings do not say it, the bot says so
- the bot does not give stock picks or investment advice

A confident wrong answer is a failure. Driftwood's business is being right.

## Tools used in this phase

| Tool | Why it is here |
| ---- | -------------- |
| PydanticAI | Runs the agent: instructions, tools, and a typed result |
| OpenAI chat model | Default `gpt-4o-mini` (`OPENAI_CHAT_MODEL`) |
| Pydantic models | `GroundedAnswer` and `Citation` in `app/assistant/outputs.py` |
| `app/grounding/validator.py` | Rejects a citation that does not match a passage retrieved in this turn |

## What one turn does

1. Build deps (`app/assistant/deps.py`): the user, the thread, the retriever, a registry of passages actually retrieved, and the validator.
2. The agent reads `app/assistant/instructions.md` and may call the Phase 5 tools, up to `ASSISTANT_MAX_TOOL_ROUNDS` (default 8).
3. It must return a `GroundedAnswer`, not free-form text the app then hopes is cited.
4. The validator checks every citation against the registry. A mismatch fails closed: the user sees a failure message instead of an uncited claim.
5. The orchestrator persists the user message, the assistant message, and `message_citations`.

The model is called only from the backend. The OpenAI API key stays in backend settings.

## How to check it

```powershell
uv run pytest -m "not integration"
uv run python -m app.scripts.preflight
```

Preflight covers env, migrations, corpus presence, and a retrieval smoke query. It does not spend a full chat completion unless you ask a question in the app.
