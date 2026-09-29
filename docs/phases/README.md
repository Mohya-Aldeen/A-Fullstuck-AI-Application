# How this project is built

Document Copilot is an internal chatbot for Driftwood Capital analysts. They ask plain-English questions about a fixed set of SEC 10-K filings and get answers that cite the filing and show the passage the claim came from.

The product is three running pieces, not one program:

| Piece | Where it runs | Job |
| ----- | ------------- | --- |
| React app | Your browser, later a Railway frontend service | Sign-in, chat screen, citation chips |
| FastAPI | Your machine, later a Railway backend service | Auth check, search, LLM, saving chats |
| Supabase Postgres | Supabase (already hosted) | Users, chats, filings, chunks, vectors |

OpenAI is a fourth outside service. The backend calls it for embeddings and for the written answer. The browser never calls OpenAI and never sees the service-role key.

These notes walk the build in the same order as [todos.md](../todos.md). Each folder has one `README.md`.

| Phase | What it adds |
| ----- | ------------ |
| [1 — Backend foundation](01-backend-foundation/README.md) | FastAPI process, config, health check, tests |
| [2 — Database](02-database/README.md) | Tables, pgvector, full-text search, migrations |
| [3 — Auth](03-auth/README.md) | Email login and JWT checks |
| [4 — Ingestion](04-ingestion/README.md) | 10-Ks turned into embedded chunks |
| [5 — Retrieval](05-retrieval/README.md) | Hybrid search that finds passages |
| [6 — Assistant](06-assistant/README.md) | Grounded answers and citation checks |
| [7 — Chat API](07-chat-api/README.md) | Threads, history, and streaming |
| [8 — Frontend](08-frontend/README.md) | The analyst UI |
| [9 — Deployment](09-deployment/README.md) | How Railway hosts the two services |
| [10 — Pilot](10-pilot/README.md) | How to judge whether the product works |

Corpus files for ingestion live in `data/downloads/` and `data/markdown/`. See [data/README.md](../../data/README.md).
