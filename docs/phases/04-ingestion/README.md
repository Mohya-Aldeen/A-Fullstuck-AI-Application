# Phase 4 — Ingestion pipeline

## Purpose

Turn public SEC filings into rows the chatbot can search. This is a batch job, not something that happens when an analyst sends a message.

The sample corpus is fixed: Apple, Microsoft, NVIDIA, Amazon, and Alphabet, five 10-Ks each, fiscal years 2021–2025. **25 filings.**

## Tools used in this phase

| Tool | Why it is here |
| ---- | -------------- |
| SEC EDGAR | Source of the HTML filings. Public domain |
| Python stdlib (`urllib`) | `data/download.py` fetches them. No extra HTTP library |
| Docling | Converts HTML into Markdown and chunks it |
| docling-core HybridChunker | Splits on document structure with an OpenAI token budget (`INGEST_CHUNK_MAX_TOKENS`, default 512) |
| OpenAI embeddings | `text-embedding-3-small`, 1536 dimensions |
| Supabase service-role client | Writes `source_documents` and `document_chunks` |

## Steps

1. `uv run data/download.py` → `data/downloads/<year>/*.html` and a manifest.
2. `uv run data/convert_to_markdown.py` → `data/markdown/` via Docling.
3. `uv run python -m ingest.load_corpus` from `backend/` → chunks, embeddings, database rows.

Each chunk keeps ticker, filing type, year, accession number, page, and section when Docling provides them. Re-running is idempotent: the same accession number is updated rather than duplicated.

`search_vector` is not written by this script. Postgres generates it from the chunk text (see Phase 2).

Downloaded HTML and Markdown are gitignored. They stay on the machine that runs ingestion. The Railway API does not need those files, because the searchable text already lives in Supabase.

## How to check it

`uv run python -m app.scripts.preflight` checks env, migrations, that chunks exist, and that a known passage can be retrieved.

Unit tests for page and section labels live in `backend/tests/ingest/test_docling_chunking.py`. The Docling conversion test is marked `integration` because it needs local filing files.
