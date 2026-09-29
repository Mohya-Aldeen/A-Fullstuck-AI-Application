# Phase 9 — Deployment on Railway

## Purpose

Run the same app somewhere other than your laptop, so an analyst can open a URL. Deployment does not add product features. It copies the two programs you already run locally onto a host that stays on.

You have not done this before, so this note explains the idea first and the clicks second.

## The idea, without Railway jargon

Right now three things are already true:

1. **Supabase** is already "deployed." You did not install Postgres on your PC. Supabase runs it, and your laptop talks to it over the internet. Chats, filings, chunks, and vectors stay there.
2. **The backend** is a Python process. Locally you start it with Uvicorn. When you close the terminal, analysts cannot use it.
3. **The frontend** is a static website after `pnpm build`. Vite turns TypeScript into files in `frontend/dist`. A browser can open those files only if some computer is serving them.

Railway's job is to be the computer that keeps the Python process running and serves `dist/`. Supabase stays Supabase. OpenAI stays OpenAI. You do not move the database onto Railway.

```text
analyst's browser
    |  HTTPS
    |-- sign in ----------> Supabase Auth
    |-- chat + JWT -------> Railway backend (FastAPI)
    |                          |-- check JWT --> Supabase Auth
    |                          |-- search rows -> Supabase Postgres
    |                          |-- write answer -> OpenAI
    |
    +-- loads HTML/JS ----> Railway frontend (the Vite build)
```

The backend stays stateless. If Railway restarts the process, no chats are lost, because they were written to Supabase.

## Words you will see in the dashboard

| Word | Meaning here |
| ---- | ------------ |
| Project | A folder in Railway. One project holds both services. |
| Service | One deployable program. You will create **two**: `backend` and `frontend`. |
| Root directory | Which folder in this git repo that service builds. `backend` or `frontend`. This repo is a monorepo, so this setting is required. |
| Variable | An environment variable, the same kind of value as in `.env`. Railway injects them into the process. They are not committed to git. |
| Deploy | Railway clones the repo, installs dependencies, builds, and starts the start command. |
| Public domain | An `https://….up.railway.app` URL Railway gives that service. |
| Pre-deploy command | A command that runs after the build and before the new process takes traffic. The backend uses it for `alembic upgrade head`. |
| Health check | Railway requests `GET /health`. If that fails, it treats the deploy as bad. |

## What happens on a backend deploy

`backend/railway.toml` tells Railway:

1. Build with Railpack (Railway's builder). It sees `uv.lock` and installs Python dependencies with uv. The first build is slow because Docling is in that same environment, even though the live API does not parse filings.
2. Pre-deploy: `uv run python -m alembic upgrade head` against `DATABASE_URL`.
3. Start: `uv run python -m app.main`, which listens on `0.0.0.0` and the `PORT` Railway sets.
4. Hit `/health` until it returns `{"status":"ok"}`.

You do not SSH into a server and run these yourself. A git push (or a redeploy button) runs them again.

## What happens on a frontend deploy

`frontend/railway.toml` starts `pnpm start`, which runs `node serve.mjs`.

That small server does two jobs:

- it serves the built files in `dist/`
- if the path is a page route (`/sign-in`, `/chat/some-id`) and not a real file, it returns `index.html` so React Router can take over

`serve.mjs` exists so we do not add a static-file library for this.

**Build-time variables.** Vite inlines every `VITE_` value when it builds. The JavaScript that reaches the browser already contains the API URL. Setting `VITE_API_BASE_URL` after the build does nothing until you redeploy the frontend. Backend variables are different: FastAPI reads them when the process starts, so a backend restart picks up a new `ALLOWED_ORIGINS`.

## Why CORS shows up again

Locally the page is `localhost:5173` and the API is `127.0.0.1:8000`. Those are different origins, and `ALLOWED_ORIGINS` allows them.

In production the page is `https://<frontend>.up.railway.app` and the API is `https://<backend>.up.railway.app`. Also different origins. If the frontend origin is missing from `ALLOWED_ORIGINS`, the browser will block the chat request and the UI will look like a network error. The API itself can be healthy.

The localhost regex in `app/main.py` does **not** allow Railway URLs. Production origins must be listed explicitly, with `https://` and no trailing slash.

## Ingestion does not run on Railway

The HTML and Markdown filings are gitignored. Railway never receives `data/downloads` or `data/markdown`.

That is fine if this Railway app uses the **same Supabase project** you already ingested into. The chunks are already in Postgres. Deploying the API just points a new Python process at that same database.

Run ingestion again only if you create a **new** Supabase project for production. Run it from your laptop, with that project's keys in `backend/.env`, via `uv run python -m ingest.load_corpus`. Do not expect the Railway service to see local filing files.

## What you do in the dashboard

The repo cannot log in to Railway for you. These steps need your Railway account and the same secrets already in your local `.env` files. Do not commit those files.

### 1. Confirm the database is already current

From `backend/` on your machine:

```powershell
uv run python -m alembic upgrade head
uv run python -m app.scripts.preflight
```

If preflight says the corpus is present, you do not need to re-ingest before the first deploy.

### 2. Create the project and the backend service

1. Sign in at [railway.com](https://railway.com) and create a project.
2. Add a service from the GitHub repo `Mohya-Aldeen/A-Fullstuck-AI-Application`.
3. Set **Root Directory** to `backend`.
4. Generate a public domain. Copy it. This is the backend URL.
5. Add variables (same values as `backend/.env`):

   - `SUPABASE_URL`
   - `SUPABASE_ANON_KEY`
   - `SUPABASE_SERVICE_ROLE_KEY`
   - `DATABASE_URL` — on Railway, the direct `db.<ref>.supabase.co` host is fine. If it fails, use the Supabase **session** pooler URI, port **5432**, not 6543.
   - `OPENAI_API_KEY`
   - `OPENAI_CHAT_MODEL` = `gpt-4o-mini`
   - `OPENAI_EMBEDDING_MODEL` = `text-embedding-3-small`
   - `OPENAI_EMBEDDING_DIMENSIONS` = `1536`
   - `ALLOWED_ORIGINS` = `http://localhost:5173` for now. You will add the frontend URL in step 5.

6. Deploy. Do not set `PORT`. Railway sets it.
7. Open `https://<backend>.up.railway.app/health`. You want `{"status":"ok"}`.

The first deploy can sit on "installing" for a long time because Docling is large. That is not a hang by itself. Read the build log if it eventually errors.

### 3. Create the frontend service

In the same project, add a second service from the same repo.

1. Root Directory = `frontend`.
2. Generate a public domain. Copy it. This is the site analysts open.
3. Variables, set **before** the first successful build:

   - `VITE_API_BASE_URL` = `https://<backend>.up.railway.app` (no trailing slash)
   - `VITE_SUPABASE_URL`
   - `VITE_SUPABASE_ANON_KEY`

4. Deploy.
5. Open the frontend URL. You should see the sign-in page, not a JSON error.

### 4. Tell Supabase about the new site

In the Supabase dashboard: **Authentication → URL configuration**.

- Site URL: the frontend Railway URL
- Redirect URLs: that same URL, and `https://<frontend>.up.railway.app/**` if you want every path allowed

Email confirmation links will otherwise send people back to localhost.

### 5. Allow the browser to call the API

On the **backend** service, set:

```text
ALLOWED_ORIGINS=http://localhost:5173,https://<frontend>.up.railway.app
```

Redeploy the backend (or restart it) so the process reads the new value. You do not rebuild the frontend for this change.

### 6. Smoke test

On the public frontend URL, not on localhost:

1. Sign up or sign in.
2. If sign-up says to check email, confirm it, then sign in. For a private pilot you can also turn off email confirmation in Supabase while you test.
3. Start a chat and ask one question from the client brief, for example how Apple's revenue mix changed from 2021 to 2025.
4. Wait until the stream finishes.
5. Click a citation and read the passage.
6. Reload the page. The thread and the citations should still be there.

`GET /health` being OK does not prove this path. The smoke test is the real check.

## What is already in the repo

| File | Role |
| ---- | ---- |
| `backend/railway.toml` | Migrate, then start Uvicorn on `PORT` |
| `frontend/railway.toml` | Serve the built site |
| `frontend/serve.mjs` | Static files plus client-side routes |
| `backend/app/config.py` | `PORT`, default 8000 locally |
| `backend/app/main.py` | Binds that port and logs each request as JSON |

## What is not done until you click through the steps

- The two Railway services do not exist yet.
- `ALLOWED_ORIGINS` on the live service does not include a production URL yet, because that URL does not exist yet.
- The smoke test has not been run against a public URL.

Pushing this repo to GitHub does not deploy it. Railway deploys when the project is connected and you deploy, or when that connection is set to deploy on push to `main`.
