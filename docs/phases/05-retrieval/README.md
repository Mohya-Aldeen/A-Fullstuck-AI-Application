# Phase 5 — Retrieval

## Purpose

Given an analyst question, return the filing passages most likely to contain the answer. The model is not allowed to "know" Apple's revenue from its training data. It has to be shown passages from this corpus.

## How hybrid search works

Two searches run separately, then a third step merges them:

1. **Semantic.** Embed the question with the same OpenAI model used at ingest. Ask Postgres (pgvector) for chunks whose vectors are nearest.
2. **Lexical.** Postgres full-text search over `search_vector` catches exact names, numbers, and phrases embeddings sometimes blur ("AWS", accession numbers, "Wearables").
3. **Reciprocal Rank Fusion** in `app/retrieval/fusion.py`. Each list has a rank. A chunk's score is `1 / (60 + rank)` from each list it appears in. Scores are added. The lists are never mixed by their raw distances, because those numbers are not on the same scale.

`app/retrieval/retriever.py` returns the fused passages plus neighboring chunks so the model sees a bit of surrounding context.

## Tools the assistant may call

These are thin wrappers in `app/retrieval/tools.py`:

- `search_filings` — hybrid search, optional filters such as ticker and year
- `read_chunk` — one chunk by id
- `read_surrounding_chunks` — neighbors of a chunk

The browser cannot call these. Only the backend agent can.

## How to check it

Unit tests cover fusion ranking and query assembly with a fake database. The live test is marked `integration` in `backend/tests/retrieval/test_integration_retrieval.py`.

`uv run python -m app.scripts.smoke_retrieval` runs a few real queries against the ingested corpus.
