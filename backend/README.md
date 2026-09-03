# Backend (FastAPI)

Document Copilot API service. Run everything from this `backend/` folder.

## Setup

```powershell
uv sync
copy .env.example .env   # then fill in real values
```

Required env vars are listed in `.env.example`. The app loads them from `backend/.env` at startup.

## Run (dev)

```powershell
uv run python -m uvicorn app.main:app --reload --port 8001
```

- API: http://127.0.0.1:8001
- Health check: http://127.0.0.1:8001/health

Use `uv run` so commands use the project venv. Plain `python` may point at system Python and fail on imports.

## Migrations

Review the pending migration in `alembic/versions/` before applying.

```powershell
# Preview current migration history (does not change the database)
uv run python -m alembic history

# Apply migrations to Supabase (changes the database)
uv run python -m alembic upgrade head
```

Use `python -m alembic` instead of bare `alembic` on Windows if Application Control blocks `.exe` shims.

Use the **direct** Supabase `DATABASE_URL` in `.env`, not the transaction pooler URL.

**Windows note:** if you get `could not translate host name` for `db.<ref>.supabase.co`, your network likely has no working IPv6. Use the **Session pooler** URI from Supabase (port **5432**) instead of the direct `db.` host.

## Tests

```powershell
uv run pytest -m "not integration"
```
