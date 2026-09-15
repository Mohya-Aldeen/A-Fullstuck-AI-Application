"""Pre–Phase 7 gate: env, schema head, corpus, retrieval smoke.

Run from backend/:

    uv run python -m app.scripts.preflight
"""

from __future__ import annotations

import asyncio
import subprocess
import sys

from app.config import settings
from app.database import documents as doc_db
from app.database.supabase import create_service_role_client

MIN_SOURCE_DOCUMENTS = 25
MIN_CHUNKS = 1_000


def _check_config() -> list[str]:
    failures: list[str] = []
    checks = {
        "SUPABASE_URL": settings.SUPABASE_URL,
        "SUPABASE_ANON_KEY": settings.SUPABASE_ANON_KEY,
        "SUPABASE_SERVICE_ROLE_KEY": settings.SUPABASE_SERVICE_ROLE_KEY,
        "DATABASE_URL": settings.DATABASE_URL,
        "OPENAI_API_KEY": settings.OPENAI_API_KEY,
    }
    for name, value in checks.items():
        lowered = value.lower()
        if not value.strip():
            failures.append(f"{name} is empty")
        elif "your-" in lowered or "sk-your" in lowered:
            failures.append(f"{name} still looks like a placeholder")
    return failures


def _check_alembic_head() -> list[str]:
    result = subprocess.run(
        [sys.executable, "-m", "alembic", "current"],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        return ["Alembic current failed — run: uv run python -m alembic upgrade head"]
    if "c4f92e7a1b6d (head)" not in result.stdout:
        return [
            "Database is not at migration head c4f92e7a1b6d — "
            "run: uv run python -m alembic upgrade head"
        ]
    return []


async def _check_corpus() -> list[str]:
    client = await create_service_role_client()
    documents = await doc_db.count_source_documents(client)
    chunks = await doc_db.count_chunks(client)
    embedded = await doc_db.count_embedded_chunks_global(client)
    failures: list[str] = []
    if documents < MIN_SOURCE_DOCUMENTS:
        failures.append(
            f"source_documents={documents} (expected at least {MIN_SOURCE_DOCUMENTS})"
        )
    if chunks < MIN_CHUNKS:
        failures.append(f"document_chunks={chunks} (expected at least {MIN_CHUNKS})")
    if embedded != chunks:
        failures.append(
            f"embedded_chunks={embedded} but total chunks={chunks} — re-run ingestion"
        )
    print(
        f"Corpus: {documents} filings, {chunks} chunks, {embedded} with embeddings"
    )
    return failures


async def _run_retrieval_smoke() -> int:
    from app.scripts.smoke_retrieval import _async_main

    return await _async_main()


async def main_async() -> int:
    print("Document Copilot preflight (Phases 5–6 gate)\n")

    failures = _check_config()
    if failures:
        print("[FAIL] Configuration")
        for item in failures:
            print(f"  - {item}")
        return 1
    print("[PASS] Configuration")

    failures = _check_alembic_head()
    if failures:
        print("[FAIL] Migrations")
        for item in failures:
            print(f"  - {item}")
        return 1
    print("[PASS] Migrations at head (c4f92e7a1b6d)")

    failures = await _check_corpus()
    if failures:
        print("[FAIL] Corpus")
        for item in failures:
            print(f"  - {item}")
        return 1
    print("[PASS] Corpus ingested and embedded")

    print()
    smoke_code = await _run_retrieval_smoke()
    if smoke_code != 0:
        return smoke_code

    print(
        "\nPreflight PASSED. Recommended manual check before Phase 7: "
        "sign in, ask a client-brief question, reload thread, confirm citations."
    )
    return 0


def main() -> None:
    raise SystemExit(asyncio.run(main_async()))


if __name__ == "__main__":
    main()
