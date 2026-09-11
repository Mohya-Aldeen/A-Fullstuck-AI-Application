# Document Copilot — implementation checklist

Work top-to-bottom. Backend first, then frontend, then deploy + pilot validation.

Reference docs: [client-brief.md](./client-brief.md) · [architecture.md](./architecture.md)

---

## Blockers / prerequisites

- [x] Create Supabase project (Auth + Postgres) — see [guides/supabase-setup.md](./guides/supabase-setup.md)
- [x] Copy `backend/.env.example` → `backend/.env` and fill in all values
- [ ] Get OpenAI API key and add to `backend/.env`
- [ ] Download sample corpus: `uv run data/download.py` (Apple, Amazon, Alphabet, Microsoft, NVIDIA 10-Ks 2021–2025)
- [ ] Confirm `data/downloads/` has filing payloads before starting ingestion

---

## Phase 1 — Backend foundation

Already scaffolded; verify locally before moving on.

- [x] FastAPI app with `/health`, CORS, `app/config.py`
- [x] Alembic init (`alembic.ini`, `env.py`, `versions/`)
- [x] SQLAlchemy `Base` in `app/database/base.py`
- [x] `uv sync` + `uv run uvicorn app.main:app --reload` runs cleanly
- [ ] `structlog` wired for structured request/error logging
- [ ] pytest layout under `backend/tests/` with `@pytest.mark.integration` convention

---

## Phase 2 — Database schema & migrations

Tables from [architecture.md § Data Model](./architecture.md#data-model). Alembic is the source of truth — do not edit tables in the Supabase dashboard.

- [x] SQLAlchemy models in `app/database/models/`:
  - [x] `profiles`
  - [x] `chat_threads`
  - [x] `chat_messages`
  - [x] `message_citations`
  - [x] `source_documents`
  - [x] `document_chunks`
- [x] Initial Alembic migration (review autogenerate output):
  - [x] `create extension if not exists vector`
  - [x] `vector(1536)` embedding column on `document_chunks`
  - [x] generated `tsvector` column + GIN index for full-text search
  - [x] HNSW index on embeddings
  - [x] RLS enabled + policies (users see only their own chats)
- [x] `uv run python -m alembic upgrade head` succeeds against Supabase
- [x] `app/database/supabase.py` — user-scoped and service-role client factories
- [x] Typed query helpers: `app/database/chats.py`
- [ ] Typed query helpers: `app/database/documents.py`

---

## Phase 3 — Auth (backend)

- [x] `app/auth/dependencies.py` — verify `Authorization: Bearer <token>` via Supabase Auth
- [x] `get_current_user` FastAPI dependency (user id + email from JWT)
- [x] Reject unauthenticated requests before any retrieval or LLM work (401)
- [x] Thread ownership checks — user cannot read another user's thread (403)

---

## Phase 4 — Ingestion pipeline

One-off scripts under `backend/ingest/`. Goal: normalized Markdown + chunked + embedded corpus in Supabase.

- [ ] SEC filing download script verified (`data/download.py`) — 10-Ks for AAPL, AMZN, GOOGL, MSFT, NVDA (2021–2025)
- [ ] HTML → normalized Markdown extraction (preserve page/section metadata)
- [ ] Chunking strategy (size + overlap; store chunk index, page, section, ticker, filing type, year, accession number)
- [ ] OpenAI embedding generation (`text-embedding-3-small`, 1536 dims)
- [ ] Write `source_documents` + `document_chunks` (+ embeddings + tsvector) to Supabase
- [ ] Idempotent re-run (skip or upsert already-ingested filings)
- [ ] Spot-check: query a known passage (e.g. Apple revenue mix) returns expected chunks
- [ ] Unit tests for chunking and metadata extraction

---

## Phase 5 — Retrieval

Hybrid search per [architecture.md § Retrieval Strategy](./architecture.md#retrieval-strategy).

- [ ] `retrieval/queries.py` — pgvector semantic search over `document_chunks.embedding`
- [ ] `retrieval/queries.py` — Postgres full-text search over `document_chunks.search_vector`
- [ ] `retrieval/fusion.py` — Reciprocal Rank Fusion in Python
- [ ] `retrieval/retriever.py` — query → ranked `SourcePassage` list (+ neighbor chunks for context)
- [ ] Agent tools: `search_filings`, `read_chunk`, `read_surrounding_chunks`
- [ ] Unit tests for RRF fusion and retriever ranking

---

## Phase 6 — LLM assistant & grounding

Trust contract from [client-brief.md § What "trust" means](./client-brief.md#what-trust-means-here).

- [ ] `assistant/outputs.py` — `GroundedAnswer`, `Citation`, `SourcePassage` Pydantic models
- [ ] `assistant/deps.py` — `DocumentAgentDeps` (user, thread, retriever, validator)
- [ ] `assistant/instructions.md` — system prompt encoding the product contract:
  - [ ] Answer only from retrieved passages
  - [ ] Cite every factual claim (filing + page)
  - [ ] Say clearly when corpus lacks evidence — never invent facts
  - [ ] No stock picks or investment advice
- [ ] `assistant/agent.py` — PydanticAI agent with typed deps + output
- [ ] `grounding/validator.py` — every citation maps to a retrieved passage; fail closed on mismatch
- [ ] Unit tests for citation extraction and grounding enforcement

---

## Phase 7 — Chat API & streaming

- [x] `chat/messages.py` — AI SDK UI message format ↔ internal types
- [x] `chat/orchestrator.py` — stub turn (stream + persist; retrieve → agent → validate later)
- [x] `chat/streaming.py` — AI SDK-compatible streaming events (text deltas; citation parts later)
- [x] `api/chat.py` routes:
  - [x] `GET /chat/threads` — list user's threads
  - [x] `POST /chat/threads` — create thread
  - [x] `GET /chat/threads/{id}/messages` — message history
  - [x] `POST /chat/stream` — streaming assistant turn (stub reply until Phase 6)
- [x] Persist user message + assistant message after successful stub run (citations + usage later)
- [x] Error responses: 401, 403, 404, 422, 502 per architecture spec
- [ ] Integration test (marked `@pytest.mark.integration`) against live Supabase + OpenAI

---

## Phase 8 — Frontend (after backend chat endpoint works)

- [x] Vite + React + TypeScript scaffold (`pnpm`, Tailwind, shadcn/ui, React Router)
- [x] `src/lib/env.ts` — validate `VITE_API_BASE_URL`, `VITE_SUPABASE_URL`, `VITE_SUPABASE_ANON_KEY`
- [x] `src/lib/supabase.ts` — browser Supabase client
- [x] `src/lib/http.ts` + `src/lib/api.ts` — fetch wrapper with bearer token injection
- [x] Email sign-in / sign-up pages (Driftwood email — no SSO)
- [x] `GET /me` — authenticated identity check so the browser JWT can be verified against FastAPI
- [x] Verify in the browser: sign in → home shows user id/email from `GET /me` (token reached the backend)
- [x] Unauthenticated `GET /me` returns 401
- [x] Chat page: thread list, message history, streaming input
- [x] Vercel AI SDK `useChat` pointed at `POST /chat/stream` with Supabase token
- [x] Citation UI — filing name, page, clickable source passage excerpt (excerpt + page for now; filing name when backend adds chunk metadata)
- [x] Empty states, streaming status, friendly error messages (network vs HTTP)
- [x] `pnpm tsc --noEmit` + `pnpm lint` clean

---

## Phase 9 — Deployment (Railway)

- [ ] Backend service on Railway (Uvicorn, env vars from `backend/.env.example`)
- [ ] Frontend static build on Railway (Vite build, env vars from `frontend/.env.example`)
- [ ] `ALLOWED_ORIGINS` includes production frontend URL
- [ ] Run `alembic upgrade head` against production Supabase before first deploy
- [ ] Re-run ingestion against production Supabase
- [ ] Smoke test: sign in → ask a sample analyst question → get cited answer with passage

---

## Phase 10 — Pilot validation (definition of done)

From [client-brief.md § Definition of done](./client-brief.md#definition-of-done): 5 senior analysts use it for a week and report ≥ 3 hours saved per analyst per week.

Manual QA against the [10 example analyst questions](./client-brief.md#example-analyst-questions):

- [ ] Q1 — Apple revenue mix 2021–2025
- [ ] Q2 — Amazon AWS vs retail profitability
- [ ] Q3 — NVIDIA Data Center demand drivers
- [ ] Q4 — Microsoft Azure / AI infrastructure language changes
- [ ] Q5 — Alphabet segment revenue trends
- [ ] Q6 — Risk-factor language changes (AI, cloud, export controls, etc.)
- [ ] Q7 — Apple & NVIDIA supplier concentration wording
- [ ] Q8 — CapEx / purchase commitments comparison
- [ ] Q9 — Geographic revenue exposures
- [ ] Q10 — Bot refuses to infer beyond filings when evidence is insufficient

Acceptance criteria per answer:

- [ ] Every factual claim has a citation (filing + page)
- [ ] Underlying passage visible for one-click verification
- [ ] No hallucinated facts — "not in corpus" when appropriate
- [ ] Past conversations persist per user

---

## Out of scope (do not build)

Trading recommendations · external data sources · multi-tenant · billing · mobile app
