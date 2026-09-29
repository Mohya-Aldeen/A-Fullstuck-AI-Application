# Phase 2 — Database schema and migrations

## Purpose

Store three kinds of data in one Postgres database:

- who the analyst is, and their private chats
- the filing corpus, split into chunks the search engine can rank
- which chunk backed each citation

Supabase hosts that Postgres. This repo does not run a database of its own.

## Tools used in this phase

| Tool | Why it is here |
| ---- | -------------- |
| Supabase Postgres | The hosted database |
| SQLAlchemy | Python description of the tables |
| Alembic | Versioned SQL migrations. The dashboard is not how schema changes ship |
| psycopg2 | Driver Alembic uses to talk to Postgres |
| pgvector | Stores embedding vectors and the HNSW index that searches them |
| Postgres full-text search | `tsvector` column plus a GIN index for keyword search |
| Row Level Security | A user can only read their own chats, even if a request is buggy |

## Tables

| Table | Holds |
| ----- | ----- |
| `profiles` | One row per Supabase auth user |
| `chat_threads` | A conversation |
| `chat_messages` | User and assistant messages |
| `message_citations` | Links from an assistant message to the chunks it cited |
| `source_documents` | One 10-K (ticker, year, accession number, URL) |
| `document_chunks` | A passage, its embedding, and its generated search vector |

`document_chunks.search_vector` is `GENERATED ALWAYS` from the chunk text. Ingestion writes the text. Postgres fills the search vector. Application code does not compute it.

Embeddings are 1536 numbers from OpenAI `text-embedding-3-small`, matching `OPENAI_EMBEDDING_DIMENSIONS`.

## Two ways the app talks to the database

SQLAlchemy models plus Alembic **change the shape** of the database (`alembic/versions/`).

The running API **reads and writes rows** through the Supabase Python client (`app/database/chats.py`, `app/database/documents.py`). That path carries the user JWT so RLS applies.

Alembic must use `DATABASE_URL` (direct host or session pooler on port 5432). Do not point migrations at the transaction pooler on port 6543.

## How to check it

From `backend/`, with `DATABASE_URL` set:

```powershell
uv run python -m alembic history
uv run python -m alembic upgrade head
```

`upgrade head` on a database that is already current is a no-op. That is what production will do on every deploy.
