# Phase 3 — Auth

## Purpose

Only a signed-in Driftwood analyst can search filings or see chats. Login is email and password. There is no Google sign-in and no company SSO.

## How a request proves who it is

1. The browser signs in with `@supabase/supabase-js`. Supabase Auth returns a session containing a JWT (a signed access token).
2. The frontend API client sends `Authorization: Bearer <token>` on every backend call.
3. `app/auth/dependencies.py` asks Supabase whether that token is real.
4. `get_current_user` exposes the user id and email to the route.
5. Thread routes also check that the thread belongs to that user.

Missing or bad token: **401**. Token is valid but the thread is someone else's: **403**.

## Keys, and who may hold them

| Secret | Who has it | What it can do |
| ------ | ---------- | -------------- |
| Supabase anon key | Browser (`VITE_SUPABASE_ANON_KEY`) | Sign in, and only the rows RLS allows for that user |
| User JWT | Browser, sent to FastAPI | Acts as that user |
| Service-role key | Backend only | Bypasses RLS. Used for ingestion and for creating a profile row. Never put this in the frontend |
| `DATABASE_URL` | Backend / Alembic only | Direct SQL, including migrations |

The anon key is public by design. The service-role key is not.

## What was built

- `frontend/src/lib/supabase.ts` — browser client
- `frontend/src/lib/auth.ts` and the sign-in / sign-up pages
- `backend/app/auth/dependencies.py`
- `GET /me` — returns `{id, email}` when the token is valid, 401 when it is not

`GET /me` is the handshake: if it works, the browser token really reached FastAPI.
