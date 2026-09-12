"""Ingest SEC filings: HTML → Docling HybridChunker → embeddings → Supabase.

Run from backend/:

    uv run python -m ingest.load_corpus --smoke-test
    uv run python -m ingest.load_corpus --chunk-only --limit 1
    uv run python -m ingest.load_corpus --force
"""

from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path
from uuid import UUID

from openai import AsyncOpenAI
from supabase import AsyncClient

from app.config import settings
from app.database.documents import (
    NewChunk,
    count_chunks,
    count_chunks_for_document,
    count_embedded_chunks_for_document,
    count_source_documents,
    delete_chunks_for_document,
    embedding_dimensions,
    get_document_by_accession,
    insert_chunks,
    insert_source_document,
    parse_embedding_vector,
    update_source_document,
)
from app.database.supabase import create_service_role_client
from ingest.corpus import Filing, load_filings
from ingest.docling_chunking import (
    SMOKE_TEST_ACCESSION,
    PreparedChunk,
    chunk_html_path,
    find_smoke_test_chunk,
)
from ingest.embed import embed_texts, embedding_client


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Load SEC 10-Ks into Supabase: chunk HTML with Docling HybridChunker, "
            "store markdown in source_documents, write document_chunks + embeddings."
        )
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Re-chunk and re-embed filings that already exist (matched by accession number).",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Ingest at most N filings.",
    )
    parser.add_argument(
        "--accession",
        default=None,
        help="Process a single filing by accession number.",
    )
    parser.add_argument(
        "--markdown-dir",
        type=Path,
        default=None,
        help="Override data/markdown location.",
    )
    parser.add_argument(
        "--downloads-dir",
        type=Path,
        default=None,
        help="Override data/downloads HTML location.",
    )
    parser.add_argument(
        "--chunk-only",
        action="store_true",
        help="Chunk and write to Supabase without calling OpenAI embeddings.",
    )
    parser.add_argument(
        "--smoke-test",
        action="store_true",
        help=(
            "End-to-end test on Apple 2021 10-K: one chunk, one embedding, one DB write."
        ),
    )
    parser.add_argument(
        "--embed-batch-size",
        type=int,
        default=64,
        help="OpenAI embedding batch size for full ingest.",
    )
    return parser.parse_args(argv)


def can_embed() -> bool:
    return settings.OPENAI_API_KEY.strip().startswith("sk-")


def chunk_metadata(filing: Filing, chunk: PreparedChunk) -> dict:
    return {
        "ticker": filing.ticker,
        "company_name": filing.company_name,
        "filing_type": filing.filing_type,
        "filing_date": filing.filing_date.isoformat(),
        "filing_year": filing.filing_year,
        "accession_number": filing.accession_number,
        "page": chunk.page_label,
        "section": chunk.section_label,
        "headings": list(chunk.headings),
        "chunker": "docling-hybrid",
        "embedding_model": settings.OPENAI_EMBEDDING_MODEL,
    }


def chunks_to_rows(
    filing: Filing,
    chunks: list[PreparedChunk],
    embeddings: list[list[float] | None],
) -> list[NewChunk]:
    return [
        NewChunk(
            chunk_index=chunk.index,
            text=chunk.text,
            token_count=chunk.token_count,
            embedding=vector,
            page_label=chunk.page_label,
            section_label=chunk.section_label,
            chunk_metadata=chunk_metadata(filing, chunk),
        )
        for chunk, vector in zip(chunks, embeddings, strict=True)
    ]


async def upsert_source_document(db: AsyncClient, filing: Filing):
    existing = await get_document_by_accession(db, filing.accession_number)
    if existing is None:
        return await insert_source_document(
            db,
            ticker=filing.ticker,
            company_name=filing.company_name,
            filing_type=filing.filing_type,
            filing_date=filing.filing_date,
            filing_year=filing.filing_year,
            accession_number=filing.accession_number,
            source_url=filing.source_url,
            markdown_content=filing.markdown_content,
        )
    return await update_source_document(
        db,
        existing.id,
        ticker=filing.ticker,
        company_name=filing.company_name,
        filing_type=filing.filing_type,
        filing_date=filing.filing_date,
        filing_year=filing.filing_year,
        source_url=filing.source_url,
        markdown_content=filing.markdown_content,
    )


async def document_is_fully_ingested(
    db: AsyncClient,
    document_id: UUID,
    *,
    require_embeddings: bool,
) -> bool:
    total = await count_chunks_for_document(db, document_id)
    if total == 0:
        return False
    if not require_embeddings:
        return True
    embedded = await count_embedded_chunks_for_document(db, document_id)
    return embedded == total


async def ingest_filing(
    filing: Filing,
    *,
    force: bool,
    chunk_only: bool,
    db: AsyncClient,
    openai_client: AsyncOpenAI | None,
    embed_batch_size: int,
    chunks: list[PreparedChunk] | None = None,
    selected_chunks: list[PreparedChunk] | None = None,
    precomputed_embeddings: list[list[float]] | None = None,
) -> str:
    prepared = chunks if chunks is not None else chunk_html_path(filing.source_html_path)
    to_write = selected_chunks if selected_chunks is not None else prepared

    existing = await get_document_by_accession(db, filing.accession_number)
    require_embeddings = (
        precomputed_embeddings is not None
        or (openai_client is not None and not chunk_only)
    )
    if existing is not None and not force:
        if await document_is_fully_ingested(
            db, existing.id, require_embeddings=require_embeddings
        ):
            return "skipped"

    print(f"  {len(prepared)} Docling chunks", flush=True)
    if precomputed_embeddings is not None:
        if len(precomputed_embeddings) != len(to_write):
            raise RuntimeError(
                "precomputed_embeddings length must match selected chunk count"
            )
        embeddings: list[list[float] | None] = list(precomputed_embeddings)
    elif chunk_only or openai_client is None:
        if not chunk_only and openai_client is None:
            print("  embeddings skipped (OPENAI_API_KEY is not a usable key)", flush=True)
        embeddings = [None] * len(to_write)
    else:
        embeddings = await embed_texts(
            openai_client,
            [chunk.embedding_text for chunk in to_write],
            batch_size=embed_batch_size,
        )

    document = await upsert_source_document(db, filing)
    if existing is not None:
        await delete_chunks_for_document(db, document.id)

    rows = chunks_to_rows(filing, to_write, embeddings)
    await insert_chunks(db, document_id=document.id, chunks=rows)
    return "ingested"


async def run_smoke_test(args: argparse.Namespace) -> int:
    accession = args.accession or SMOKE_TEST_ACCESSION
    if not can_embed():
        print("Smoke test requires a real OPENAI_API_KEY in backend/.env", file=sys.stderr)
        return 1

    filings = load_filings(
        args.markdown_dir,
        args.downloads_dir,
        accession_number=accession,
    )
    filing = filings[0]
    print(f"Smoke test filing: {filing.ticker} {filing.filing_year} {filing.accession_number}")

    chunks = chunk_html_path(filing.source_html_path)
    selected = find_smoke_test_chunk(chunks)
    print(
        f"Selected chunk index={selected.index} tokens={selected.token_count} "
        f"section={selected.section_label!r} page={selected.page_label!r}",
        flush=True,
    )

    db = await create_service_role_client()
    openai_client = embedding_client()
    preview_vectors = await embed_texts(openai_client, [selected.embedding_text], batch_size=1)
    if len(preview_vectors[0]) != settings.OPENAI_EMBEDDING_DIMENSIONS:
        print(
            f"Smoke test FAILED: OpenAI returned {len(preview_vectors[0])} dims "
            f"(expected {settings.OPENAI_EMBEDDING_DIMENSIONS})",
            file=sys.stderr,
        )
        return 1

    await ingest_filing(
        filing,
        force=True,
        chunk_only=False,
        db=db,
        openai_client=openai_client,
        embed_batch_size=1,
        chunks=chunks,
        selected_chunks=[selected],
        precomputed_embeddings=preview_vectors,
    )

    document = await get_document_by_accession(db, filing.accession_number)
    if document is None:
        print("Smoke test FAILED: source document missing after write", file=sys.stderr)
        return 1

    total = await count_chunks_for_document(db, document.id)
    embedded = await count_embedded_chunks_for_document(db, document.id)
    if total != 1 or embedded != 1:
        print(
            f"Smoke test FAILED: expected 1 embedded chunk, got total={total} embedded={embedded}",
            file=sys.stderr,
        )
        return 1

    response = await (
        db.table("document_chunks")
        .select("text,embedding,page_label,section_label,token_count,chunk_metadata")
        .eq("document_id", str(document.id))
        .limit(1)
        .execute()
    )
    row = (response.data or [None])[0]
    if row is None:
        print("Smoke test FAILED: chunk row missing", file=sys.stderr)
        return 1

    raw_embedding = row.get("embedding")
    embedding = parse_embedding_vector(raw_embedding)
    dims = embedding_dimensions(raw_embedding)
    if embedding is None or dims != settings.OPENAI_EMBEDDING_DIMENSIONS:
        print(
            f"Smoke test FAILED: embedding dims={dims} "
            f"(expected {settings.OPENAI_EMBEDDING_DIMENSIONS})",
            file=sys.stderr,
        )
        return 1

    text = row.get("text") or ""
    if "191,973" not in text or "iPhone" not in text:
        print("Smoke test FAILED: chunk text missing expected Apple revenue passage", file=sys.stderr)
        return 1

    print(
        f"Smoke test PASSED: 1 chunk written with {dims}-dim embedding "
        f"(section={row.get('section_label')!r}, page={row.get('page_label')!r})",
        flush=True,
    )
    return 0


async def run(args: argparse.Namespace) -> int:
    if args.smoke_test:
        return await run_smoke_test(args)

    filings = load_filings(
        args.markdown_dir,
        args.downloads_dir,
        accession_number=args.accession,
    )
    if args.limit is not None:
        filings = filings[: args.limit]
    if not filings:
        print("No filings to ingest.", file=sys.stderr)
        return 1

    print(f"Loaded {len(filings)} filing(s) from corpus.", flush=True)
    db = await create_service_role_client()
    print("Connected to Supabase with the service-role client.", flush=True)

    openai_client: AsyncOpenAI | None = None
    if args.chunk_only:
        print("Chunk-only mode: skipping OpenAI embeddings.", flush=True)
    elif can_embed():
        openai_client = embedding_client()
    else:
        print(
            "OPENAI_API_KEY is not set to a real key; "
            "writing source_documents and chunks without embeddings.",
            flush=True,
        )

    ingested = 0
    skipped = 0
    failed: list[str] = []

    for index, filing in enumerate(filings, start=1):
        label = f"{filing.ticker} {filing.filing_year} {filing.accession_number}"
        print(f"[{index}/{len(filings)}] {label}", flush=True)
        try:
            result = await ingest_filing(
                filing,
                force=args.force,
                chunk_only=args.chunk_only,
                db=db,
                openai_client=openai_client,
                embed_batch_size=args.embed_batch_size,
            )
        except Exception as exc:  # noqa: BLE001 — batch job; continue on single-file failure
            failed.append(label)
            print(f"  failed: {exc}", file=sys.stderr, flush=True)
            continue
        if result == "skipped":
            skipped += 1
            print("  skipped (already ingested)", flush=True)
        else:
            ingested += 1
            print("  ingested", flush=True)

    print(
        f"Done. ingested={ingested} skipped={skipped} failed={len(failed)} "
        f"documents={await count_source_documents(db)} chunks={await count_chunks(db)}",
        flush=True,
    )
    if failed:
        print("Failed filings:", file=sys.stderr)
        for label in failed:
            print(f"  {label}", file=sys.stderr)
        return 1
    return 0


def main(argv: list[str] | None = None) -> int:
    return asyncio.run(run(parse_args(argv)))


if __name__ == "__main__":
    raise SystemExit(main())
