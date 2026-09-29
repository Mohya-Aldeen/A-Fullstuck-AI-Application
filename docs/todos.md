# Document Copilot — implementation checklist

Work top-to-bottom. Backend first, then frontend, then deploy + pilot validation.

Reference docs: [client-brief.md](./client-brief.md) · [architecture.md](./architecture.md)

---

## Current status (local dev)

**Working end-to-end (grounded assistant):** sign in → create thread → send message → hybrid retrieval + PydanticAI answer → citations on reload.

| Layer | Done | Not yet |
| ----- | ---- | ------- |
| **Backend** | `/health`, `/me`, chat API, auth + RLS, ingestion, hybrid retrieval, PydanticAI agent + grounding, citation persist, token streaming, live chat integration test | — |
| **Frontend** | Auth, chat UI, `useChat` → FastAPI, thread list, streaming, Trust UI (citation chips + source panel) | Browser check that a citation passage matches the filing |
| **Data** | 25 filings ingested into the existing Supabase project | Re-ingest only if you create a new production database |
| **Deploy** | Railway config in the repo (`railway.toml`, `serve.mjs`) | The two Railway services, created in your account |

**Next recommended phase:** Phase 9 — deploy the two Railway services, then run the Phase 10 pilot. Phases 1–8 are implemented. Phase 9's Railway config is in the repo; the services themselves are created in the Railway dashboard. Phase 10 is a week of analyst use, not more code. See [phases/README.md](./phases/README.md).

**Verified locally (automated):** `uv run python -m app.scripts.preflight` · `uv run pytest` (48 tests) · `pnpm tsc --noEmit` · `pnpm lint` (warnings only).

**Manual gate before Phase 7:** browser sign-in → one client-brief question → stream completes → reload shows citations.

---

## Blockers / prerequisites

- [x] Create Supabase project (Auth + Postgres) — see [guides/supabase-setup.md](./guides/supabase-setup.md)
- [x] Copy `backend/.env.example` → `backend/.env` and fill in all values
- [x] Get OpenAI API key and add to `backend/.env`
- [x] Download sample corpus: `uv run data/download.py` (Apple, Amazon, Alphabet, Microsoft, NVIDIA 10-Ks 2021–2025)
- [x] Confirm `data/downloads/` has filing payloads before starting ingestion

---

## Phase 1 — Backend foundation

Already scaffolded; verify locally before moving on.

- [x] FastAPI app with `/health`, CORS, `app/config.py`
- [x] Alembic init (`alembic.ini`, `env.py`, `versions/`)
- [x] SQLAlchemy `Base` in `app/database/base.py`
- [x] `uv sync` + `uv run uvicorn app.main:app --reload` runs cleanly
- [x] `structlog` wired for structured request/error logging
- [x] pytest layout under `backend/tests/` (chat unit tests in `tests/chat/`)
- [x] `@pytest.mark.integration` convention + live Supabase/OpenAI integration tests

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
- [x] Typed query helpers: `app/database/chats.py` (explicit UUIDs on insert; service-role profile bootstrap)
- [x] Typed query helpers: `app/database/documents.py`

---

## Phase 3 — Auth (backend)

- [x] `app/auth/dependencies.py` — verify `Authorization: Bearer <token>` via Supabase Auth
- [x] `get_current_user` FastAPI dependency (user id + email from JWT)
- [x] Reject unauthenticated requests before any retrieval or LLM work (401)
- [x] Thread ownership checks — user cannot read another user's thread (403)

---

## Phase 4 — Ingestion pipeline

One-off **batch scripts** under `backend/ingest/` (not the chat agent). Goal: normalized Markdown → chunks → embeddings → Supabase.

**Sample corpus (fixed scope):** 5 companies × 5 fiscal years = **25 ten-Ks** — AAPL, AMZN, GOOGL, MSFT, NVDA (2021–2025). `data/download.py` already targets this (`TICKERS` × `FILINGS_PER_COMPANY`).

**CLI shape:** one entry point is enough, e.g. `uv run python -m ingest.load_corpus` (or a small `ingest/run.py` that calls parse → chunk → embed → write). Separate modules are fine; you do not need multiple manual steps every time.

**Full-text search (`search_vector`):** do **not** populate in ingest. Alembic defines `search_vector` as `GENERATED ALWAYS AS (to_tsvector('english', text)) STORED` — writing chunk `text` is enough; Postgres fills the tsvector for hybrid search in Phase 5.

- [x] Verify SEC download: `uv run data/download.py` → `data/downloads/` + `manifest.json` (25 filings)
- [x] HTML → Markdown: `uv run data/convert_to_markdown.py` → `data/markdown/` + `manifest.json` (Docling; same year layout)
- [x] Ingestion reads `data/markdown/` (preserve page/section metadata from Docling output where available)
- [x] Chunking strategy (size + overlap; store chunk index, page, section, ticker, filing type, year, accession number)
- [x] OpenAI embedding generation (`text-embedding-3-small`, 1536 dims)
- [x] Write `source_documents` + `document_chunks` (text + embedding; `search_vector` auto-generated)
- [x] Idempotent re-run (skip or upsert by accession number)
- [x] **Spot-check gate (required before Phase 5):** confirm chunks exist in Supabase and a known passage retrieves correctly — e.g. Apple revenue mix / segment table language from Q1 in [client-brief.md](./client-brief.md)
- [x] Unit tests for chunking and metadata extraction

---

## Phase 5 — Retrieval

**Goal:** a user question returns ranked, relevant source passages.

Hybrid search per [architecture.md § Retrieval Strategy](./architecture.md#retrieval-strategy).

- [x] `retrieval/queries.py` — pgvector semantic search over `document_chunks.embedding`
- [x] `retrieval/queries.py` — Postgres full-text search over `document_chunks.search_vector`
- [x] `retrieval/fusion.py` — Reciprocal Rank Fusion in Python
- [x] `retrieval/retriever.py` — query → ranked passage list (+ neighbor chunks for context); use a minimal retrieval type here or import `SourcePassage` once Phase 6 models land
- [x] Agent tools: `search_filings`, `read_chunk`, `read_surrounding_chunks` (thin wrappers over the retriever)
- [x] Unit tests: RRF fusion ranking
- [x] Unit tests: query assembly with mocked DB (no network)
- [x] Integration test (`@pytest.mark.integration`, optional): real hybrid query against ingested corpus
- [x] **Retrieval gate (required before Phase 6):** 2–3 scripted or manual queries from [client-brief.md](./client-brief.md) return relevant chunks (e.g. Apple revenue mix, AWS profitability language)

---

## Phase 6 — LLM assistant & grounding

Trust contract from [client-brief.md § What "trust" means](./client-brief.md#what-trust-means-here).

- [x] `assistant/outputs.py` — `GroundedAnswer`, `Citation` (passages stay in `retrieval.models.SourcePassage`)
- [x] `assistant/deps.py` — `DocumentAgentDeps` (user, thread, instrumented tools, registry, validator)
- [x] `assistant/instructions.md` — system prompt encoding the product contract:
  - [x] Answer only from retrieved passages
  - [x] Cite every factual claim (filing + page)
  - [x] Say clearly when corpus lacks evidence — never invent facts
  - [x] No stock picks or investment advice
- [x] `assistant/agent.py` — PydanticAI agent with retrieval tools + `GroundedAnswer` output
- [x] `app/embeddings.py` — shared query/batch embeddings (retrieval + ingest)
- [x] `OPENAI_CHAT_MODEL` / `ASSISTANT_MAX_TOOL_ROUNDS` in `app/config.py`
- [x] `grounding/validator.py` — every citation maps to a retrieved passage; fail closed on mismatch
- [x] `chat/orchestrator.py` — agent turn → validate → stream → persist `message_citations`
- [x] Unit tests: grounding, assistant outputs/tools, orchestrator (mocked agent)
- [x] **Preflight script:** `uv run python -m app.scripts.preflight` (env + migrations + corpus + retrieval smoke)

---

## Phase 7 — Chat API & streaming

- [x] `chat/messages.py` — AI SDK UI message format ↔ internal types
- [x] `chat/orchestrator.py` — full turn (agent → validate → stream → persist)
- [x] `chat/streaming.py` — AI SDK-compatible streaming events (text deltas; citation parts later)
- [x] `api/chat.py` routes:
  - [x] `GET /chat/threads` — list user's threads
  - [x] `POST /chat/threads` — create thread
  - [x] `GET /chat/threads/{id}/messages` — message history
  - [x] `POST /chat/stream` — streaming grounded assistant turn
- [x] Persist user message + assistant message after successful grounded run (citations persisted; usage metadata later)
- [x] Error responses: 401, 403, 404, 422, 502 per architecture spec
- [x] Integration test (marked `@pytest.mark.integration`) against live Supabase + OpenAI

---

## Phase 8 — Frontend (after backend chat endpoint works)

- [x] Vite + React + TypeScript scaffold (`pnpm`, Tailwind, shadcn/ui, React Router)
- [x] `src/lib/env.ts` — validate `VITE_API_BASE_URL`, `VITE_SUPABASE_URL`, `VITE_SUPABASE_ANON_KEY`
- [x] `src/lib/supabase.ts` — browser Supabase client
- [x] `src/lib/http.ts` + `src/lib/api.ts` — fetch wrapper with bearer token injection
- [x] Email sign-in / sign-up pages (Driftwood email — no SSO)
- [x] `GET /me` — authenticated identity check so the browser JWT can be verified against FastAPI
- [x] Verify in the browser: sign in → `GET /me` returns user id/email (token reached the backend)
- [x] Unauthenticated `GET /me` returns 401
- [x] `/` and `/chat/:threadId` — chat app (legacy `HomePage.tsx` unused)
- [x] Chat page: thread list, message history, streaming input
- [x] Verify in the browser: New chat → send message → stub stream → reload shows history
- [x] Vercel AI SDK `useChat` pointed at `POST /chat/stream` with Supabase token
- [x] **Trust UI (citations & source passages):**
  - [x] Citation chips on assistant messages (ticker, filing type, year, page/section via chunk + `source_documents` join)
  - [x] Source passage panel — click a chip to show verbatim excerpt + SEC link
  - [x] Empty states (no threads, no messages, thread not found)
  - [x] Error states — session expired (401), access denied (403), retrieval/DB (502), network/CORS; grounding failure copy on assistant message
  - [x] Loading/streaming status during assistant run
  - [ ] Verify in browser: click citation → exact passage matches filing excerpt
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
