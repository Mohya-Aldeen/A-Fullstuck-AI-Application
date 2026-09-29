# Phase 1 — Backend foundation

## Purpose

Give the product a Python server that starts, refuses to boot when configuration is missing, and can say "I am alive." Nothing about filings or chat exists yet. Later phases hang off this process.

## What you are looking at

The backend is a **FastAPI** app started by **Uvicorn**. FastAPI turns Python functions into HTTP routes. Uvicorn is the process that listens on a port and hands requests to FastAPI.

Locally that process is on your laptop (`http://127.0.0.1:8000`). In production the same process runs on Railway and listens on whatever port Railway assigns.

## Tools used in this phase

| Tool | Why it is here |
| ---- | -------------- |
| Python 3.12 | The backend language |
| uv | Installs dependencies and runs commands in the project environment |
| FastAPI | HTTP API |
| Uvicorn | Serves the API |
| Pydantic + pydantic-settings | Reads `backend/.env` into one `settings` object |
| structlog | Writes one JSON log line per request so Railway logs are readable |
| pytest | Backend tests |
| Ruff | Linter |

`app/config.py` is the only place that reads environment variables. If `SUPABASE_URL` or `OPENAI_API_KEY` is missing, import fails immediately. That is intentional: a half-configured server is worse than a server that will not start.

## What was built

- `backend/app/main.py` — app, CORS, request logs, `GET /health`
- `backend/app/config.py` — settings
- `backend/pyproject.toml` — dependencies
- `backend/tests/` — pytest layout, including `@pytest.mark.integration` for tests that need live Supabase or OpenAI

`GET /health` returns `{"status":"ok"}`. It does not check the database. Railway uses it only to decide whether the process is up.

CORS is the browser rule that blocks a web page on one origin from calling an API on another. Locally the page is `http://localhost:5173` and the API is `http://127.0.0.1:8000`. `ALLOWED_ORIGINS` lists the pages that are allowed to call the API.

## How to check it

From `backend/`:

```powershell
uv sync
uv run python -m uvicorn app.main:app --reload --port 8001
```

Open `http://127.0.0.1:8001/health`. You should see `{"status":"ok"}`.

Fast tests (no network):

```powershell
uv run pytest -m "not integration"
```
