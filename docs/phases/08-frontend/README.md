# Phase 8 — Frontend

## Purpose

The analyst's desk: sign in with email, ask a question, watch the answer stream, and check a citation against the filing passage. The page does not search, embed, or call OpenAI. It renders state and talks to FastAPI.

## Tools used in this phase

| Tool | Why it is here |
| ---- | -------------- |
| Vite | Dev server and production build |
| React 19 + TypeScript | UI |
| React Router | `/sign-in`, `/sign-up`, `/`, `/chat/:threadId` |
| Tailwind CSS | Styling |
| shadcn/ui + Base UI + Lucide | Buttons, inputs, icons |
| `@supabase/supabase-js` | Email session in the browser |
| `ai` and `@ai-sdk/react` | `useChat` against `POST /chat/stream` |
| pnpm | The only package manager. Lockfile is `pnpm-lock.yaml` |
| Oxlint | `pnpm lint` |

There is no frontend test runner. Checks are `pnpm tsc --noEmit`, `pnpm lint`, and using the app in a browser.

HTTP uses `fetch` through `src/lib/http.ts` and `src/lib/api.ts`. The API client attaches the Supabase access token. Components do not handle tokens.

`src/lib/env.ts` is the only module that reads `import.meta.env`. Required values:

- `VITE_API_BASE_URL` — FastAPI origin
- `VITE_SUPABASE_URL`
- `VITE_SUPABASE_ANON_KEY`

Anything named `VITE_` is compiled into the static JavaScript. That matters in Phase 9: changing the API URL means rebuilding the frontend, not only restarting it.

## Trust UI

- Citation chips on an assistant message (ticker, filing, year, page or section)
- A source panel with the verbatim excerpt and a link to the SEC filing
- Empty states for no threads, no messages, and an unknown thread
- Error copy for 401, 403, 502, network/CORS failures, and a grounding failure

## How to check it

```powershell
cd frontend
pnpm install
pnpm dev
```

Sign in, open a chat, ask one question from [the client brief](../../client-brief.md), then click a citation and confirm the excerpt matches the filing. Reload and confirm the thread is still there.

`pnpm tsc --noEmit` and `pnpm lint` should pass before a production build.
