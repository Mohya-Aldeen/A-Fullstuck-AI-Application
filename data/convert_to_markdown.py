# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "docling==2.125.0",
# ]
# ///
"""Convert downloaded SEC HTML filings to Markdown with Docling.

Reads `data/downloads/` (and its manifest.json when present), writes parallel
output under `data/markdown/` with the same year-based folder layout.

Run from the repo root:

    uv run data/convert_to_markdown.py

See https://docling-project.github.io/docling/
"""

from __future__ import annotations

import json
import shutil
import sys
from datetime import UTC, datetime
from pathlib import Path

from docling.datamodel.base_models import ConversionStatus
from docling.document_converter import DocumentConverter

DATA_DIR = Path(__file__).resolve().parent
INPUT_DIR = DATA_DIR / "downloads"
OUTPUT_DIR = DATA_DIR / "markdown"
INPUT_MANIFEST = INPUT_DIR / "manifest.json"
OUTPUT_MANIFEST = OUTPUT_DIR / "manifest.json"

# Params: edit these, then run `uv run data/convert_to_markdown.py`
CLEAR_OUTPUT_DIR = False
SKIP_EXISTING = True
HTML_SUFFIXES = {".html", ".htm", ".xhtml"}


def load_input_manifest() -> dict | None:
    if not INPUT_MANIFEST.is_file():
        return None
    return json.loads(INPUT_MANIFEST.read_text(encoding="utf-8"))


def discover_html_files() -> list[Path]:
    files: list[Path] = []
    for path in sorted(INPUT_DIR.rglob("*")):
        if path.is_file() and path.suffix.lower() in HTML_SUFFIXES:
            files.append(path)
    return files


def markdown_relative_path(html_relative: str) -> str:
    path = Path(html_relative)
    return str(path.with_suffix(".md"))


def convert_html(converter: DocumentConverter, html_path: Path) -> str:
    result = converter.convert(html_path)
    if result.status != ConversionStatus.SUCCESS:
        raise RuntimeError(f"Docling conversion failed with status {result.status!s}")
    if result.document is None:
        raise RuntimeError("Docling returned no document")
    return result.document.export_to_markdown()


def filing_from_path(html_path: Path) -> dict:
    relative = html_path.relative_to(INPUT_DIR).as_posix()
    return {
        "source_html_path": relative,
        "markdown_path": markdown_relative_path(relative),
    }


def convert_all() -> dict:
    if not INPUT_DIR.is_dir():
        raise SystemExit(
            f"Input directory not found: {INPUT_DIR}\n"
            "Run `uv run data/download.py` first."
        )

    if CLEAR_OUTPUT_DIR and OUTPUT_DIR.exists():
        shutil.rmtree(OUTPUT_DIR)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    source_manifest = load_input_manifest()
    converter = DocumentConverter()

    output = {
        "source": "SEC EDGAR HTML via Docling",
        "source_manifest": str(INPUT_MANIFEST.relative_to(DATA_DIR)),
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "converted_count": 0,
        "skipped_count": 0,
        "failed_count": 0,
        "filings": [],
    }

    if source_manifest is not None:
        entries = source_manifest.get("filings", [])
    else:
        print(f"No manifest at {INPUT_MANIFEST}; scanning HTML files under {INPUT_DIR}")
        entries = [filing_from_path(path) for path in discover_html_files()]

    total = len(entries)
    for index, entry in enumerate(entries, start=1):
        html_rel = entry.get("local_path") or entry.get("source_html_path")
        if not html_rel:
            print(f"[{index}/{total}] Skipping entry without html path: {entry}", file=sys.stderr)
            continue

        html_path = INPUT_DIR / html_rel
        md_rel = markdown_relative_path(html_rel)
        md_path = OUTPUT_DIR / md_rel

        record = dict(entry)
        record["source_html_path"] = Path(html_rel).as_posix()
        record["markdown_path"] = md_rel

        label = record.get("ticker") or html_path.name
        print(f"[{index}/{total}] {label} -> {md_rel}")

        if not html_path.is_file():
            record["status"] = "failed"
            record["error"] = f"Missing source HTML: {html_path}"
            output["failed_count"] += 1
            output["filings"].append(record)
            print(f"  missing: {html_path}", file=sys.stderr)
            continue

        if SKIP_EXISTING and md_path.is_file():
            record["status"] = "skipped"
            output["skipped_count"] += 1
            output["filings"].append(record)
            print("  skipped (already converted)")
            continue

        try:
            markdown = convert_html(converter, html_path)
            md_path.parent.mkdir(parents=True, exist_ok=True)
            md_path.write_text(markdown, encoding="utf-8")
            record["status"] = "converted"
            record["markdown_bytes"] = md_path.stat().st_size
            output["converted_count"] += 1
        except Exception as exc:  # noqa: BLE001 — batch job; continue on single-file failure
            record["status"] = "failed"
            record["error"] = str(exc)
            output["failed_count"] += 1
            print(f"  failed: {exc}", file=sys.stderr)

        output["filings"].append(record)

    OUTPUT_MANIFEST.write_text(json.dumps(output, indent=2) + "\n", encoding="utf-8")
    return output


if __name__ == "__main__":
    result = convert_all()
    print(
        f"Converted {result['converted_count']} filing(s) to {OUTPUT_DIR} "
        f"({result['skipped_count']} skipped, {result['failed_count']} failed)"
    )
    print(f"Manifest: {OUTPUT_MANIFEST}")
