# Tools, languages, and services

Inventory of everything this project uses to build and run Document Copilot. Versions are the ones pinned in `backend/pyproject.toml` and `frontend/package.json` unless noted.

For setup and how to run the app, see [README.md](README.md).

---

## Programming languages

| Language | Where | Role |
| -------- | ----- | ---- |
| **Python 3.12+** | `backend/`, `data/` | API, ingestion, retrieval, tests, corpus scripts |
| **TypeScript** | `frontend/src/` | React SPA source |
| **HTML** | `frontend/index.html`, SEC filings in `data/downloads/` | App shell; raw corpus format |
| **CSS** | `frontend/src/index.css` | Global theme tokens + Tailwind entry |
| **SQL** | `backend/alembic/versions/` | Schema, indexes, RLS, retrieval RPCs |
| **Markdown** | `docs/`, `backend/app/assistant/instructions.md` | Specs and agent instructions |
| **JSON** | env examples, manifests, lockfiles, shadcn config | Config and data manifests |
| **TOML** | `backend/pyproject.toml` | Python project + dependencies |
| **YAML** | `frontend/pnpm-lock.yaml` | Frontend lockfile |

JavaScript is not written as app source. The frontend compiles TypeScript to JS via Vite.

---

## External services and platforms

| Tool | Layer | Used for |
| ---- | ----- | -------- |
| **Supabase** | Shared | Hosted Postgres, Auth, project dashboard |
| **PostgreSQL** | Database | Users, chats, documents, chunks |
| **pgvector** | Database | Semantic (vector) search |
| **Postgres full-text search** | Database | Keyword retrieval (`tsvector` + GIN) |
| **Supabase Auth** | Auth | Email sign-in / JWT sessions |
| **OpenAI** | AI | Chat (`gpt-4o-mini`) and embeddings (`text-embedding-3-small`, 1536 dims) |
| **Railway** | Hosting | Planned deploy: frontend service + backend service |
| **SEC EDGAR** | Data | Sample 10-K corpus via `data/download.py` |
| **Git** | Repo | Version control |

---

## Toolchain (install these on a machine)

| Tool | Version | Used for |
| ---- | ------- | -------- |
| **Python** | 3.12+ | Backend runtime |
| **uv** | latest | Backend deps, venv, `uv run` scripts |
| **Hatchling** | via uv | Python package build backend |
| **Node.js** | 20+ (LTS) | Frontend toolchain |
| **pnpm** | latest | Frontend package manager (`pnpm-lock.yaml` only) |
| **Git** | any | Source control |

---

## Backend (`backend/`)

### Runtime and framework

| Tool | Version | Used for |
| ---- | ------- | -------- |
| **FastAPI** | 0.141.1 | HTTP API (`fastapi[standard]`) |
| **Uvicorn** | 0.52.4 | ASGI server (`uvicorn[standard]`) |
| **Pydantic** | 2.13.4 | Request/response and domain models |
| **pydantic-settings** | 2.15.0 | Env/config (`app/config.py`) |
| **httpx** | 0.28.1 | Outbound HTTP |
| **structlog** | 26.1.0 | Structured logging |

### Database and auth

| Tool | Version | Used for |
| ---- | ------- | -------- |
| **SQLAlchemy** | 2.0.52 | Table models |
| **Alembic** | 1.19.1 | Migrations |
| **psycopg2-binary** | 2.9.11 | Postgres driver |
| **pgvector** (Python) | 0.5.0 | Vector column types |
| **supabase** (Python client) | 2.31.0 | Auth verification + DB access |

### AI, documents, and retrieval

| Tool | Version | Used for |
| ---- | ------- | -------- |
| **OpenAI Python SDK** | 3.3.0 | LLM + embeddings |
| **PydanticAI** | 2.32.0 | Typed agent, tools, grounded answers |
| **Docling** | 2.125.0 | HTML → Markdown conversion |
| **docling-core** | 2.94.1 | Hybrid chunking (`chunking-openai` extra) |

### Backend quality / dev

| Tool | Version | Used for |
| ---- | ------- | -------- |
| **pytest** | 9.1.1 | Unit and integration tests |
| **Ruff** | 0.16.3 | Lint / format |
| **ipykernel** | 7.3.0 | Jupyter kernels using the backend venv |

---

## Frontend (`frontend/`)

### Runtime and framework

| Tool | Version | Used for |
| ---- | ------- | -------- |
| **React** | 19.2.8 | UI |
| **react-dom** | 19.2.8 | DOM renderer |
| **Vite** | 8.2.2 | Dev server and production build |
| **TypeScript** | ~6.0.2 | Types + `tsc -b` before build |
| **@vitejs/plugin-react** | 6.1.0 | React plugin (Oxc) |
| **react-router-dom** | 7.18.3 | Client routing |
| **@types/react**, **@types/react-dom**, **@types/node** | matching | Type definitions |

### UI

| Tool | Version | Used for |
| ---- | ------- | -------- |
| **Tailwind CSS** | 4.3.3 | Styling |
| **@tailwindcss/vite** | 4.3.3 | Tailwind Vite plugin |
| **shadcn** | 4.21.0 | UI primitives (`pnpm dlx shadcn@latest add`) |
| **@base-ui/react** | 1.8.0 | Headless primitives under shadcn |
| **lucide-react** | 1.41.0 | Icons |
| **@fontsource-variable/geist** | 5.3.0 | Geist font |
| **class-variance-authority** | 0.7.1 | Component variants |
| **cn** | 0.2.6 | `className` merge helper |
| **tw-animate-css** | 1.4.0 | Animation utilities |

### Auth and chat client

| Tool | Version | Used for |
| ---- | ------- | -------- |
| **@supabase/supabase-js** | 2.114.0 | Browser auth / session |
| **ai** | 7.0.97 | Vercel AI SDK (streaming protocol) |
| **@ai-sdk/react** | 4.0.100 | `useChat` and chat UI state |

HTTP to the backend uses the browser **`fetch` API** (no axios).

### Frontend quality / config

| Tool | Version | Used for |
| ---- | ------- | -------- |
| **Oxlint** | 1.79.0 | Lint (`pnpm lint`) |
| **`.npmrc` `minimum-release-age`** | 7 days | Block brand-new npm publishes |

There is **no frontend test runner** (no Vitest, Playwright, or Cypress).

---

## Data pipeline (`data/` + `backend/ingest/`)

| Tool | Used for |
| ---- | -------- |
| **Python stdlib** (`urllib`, `json`, `pathlib`) | Download 10-K HTML from SEC EDGAR |
| **Docling** | Convert HTML filings to Markdown |
| **OpenAI embeddings** | Embed chunks (`text-embedding-3-small`) |
| **Supabase / Postgres** | Store documents, chunks, vectors, and FTS columns |

---

## Database features (Postgres / Supabase)

These are not separate products, but they are part of how the app is built:

- **`vector` extension** (`pgvector`) and **HNSW** index on embeddings
- Generated **`tsvector`** column + **GIN** index for full-text search
- **Row Level Security (RLS)** so users only see their own chats
- Hybrid retrieval: vector search + keyword search, fused in Python with **Reciprocal Rank Fusion (RRF)**

---

## Not in this project

These are commonly assumed and are **not** used:

- Django, Flask, Next.js, SSR
- npm / Yarn as the frontend package manager
- axios, lodash, Redux, Zustand
- Vitest, Playwright, Cypress
- Docker (no Dockerfile in the repo)
- Google sign-in / SSO
