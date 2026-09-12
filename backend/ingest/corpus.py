"""Load SEC filing metadata, HTML sources, and normalized Markdown."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import date
from pathlib import Path

COMPANY_NAMES = {
    "AAPL": "Apple Inc.",
    "MSFT": "Microsoft Corporation",
    "NVDA": "NVIDIA Corporation",
    "AMZN": "Amazon.com, Inc.",
    "GOOGL": "Alphabet Inc.",
}

_FILENAME_RE = re.compile(
    r"(?P<ticker>[a-z0-9]+)_"
    r"(?P<form>10-k)_"
    r"(?P<filing_date>\d{4}-\d{2}-\d{2})_"
    r"(?P<accession>.+)\.(?:md|html?|xhtml)",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class Filing:
    ticker: str
    company_name: str
    filing_type: str
    filing_date: date
    filing_year: int
    accession_number: str
    source_url: str
    source_html_path: Path
    markdown_path: Path
    markdown_content: str


def default_markdown_dir() -> Path:
    return Path(__file__).resolve().parents[2] / "data" / "markdown"


def default_downloads_dir() -> Path:
    return Path(__file__).resolve().parents[2] / "data" / "downloads"


def load_filings(
    markdown_dir: Path | None = None,
    downloads_dir: Path | None = None,
    *,
    accession_number: str | None = None,
) -> list[Filing]:
    markdown_root = markdown_dir or default_markdown_dir()
    downloads_root = downloads_dir or default_downloads_dir()
    if not markdown_root.is_dir():
        raise FileNotFoundError(
            f"Markdown corpus not found: {markdown_root}\n"
            "Run `uv run data/convert_to_markdown.py` from the repo root first."
        )

    manifest_path = markdown_root / "manifest.json"
    if manifest_path.is_file():
        entries = _filings_from_manifest(markdown_root, downloads_root, manifest_path)
    else:
        entries = _filings_from_paths(markdown_root, downloads_root)

    if accession_number is not None:
        entries = [f for f in entries if f.accession_number == accession_number]
        if not entries:
            raise FileNotFoundError(
                f"No filing with accession number {accession_number!r} in corpus."
            )

    missing_md = [f.markdown_path for f in entries if not f.markdown_path.is_file()]
    if missing_md:
        preview = "\n".join(f"  {path}" for path in missing_md[:5])
        raise FileNotFoundError(
            f"{len(missing_md)} markdown file(s) listed in the corpus are missing:\n{preview}"
        )

    missing_html = [f.source_html_path for f in entries if not f.source_html_path.is_file()]
    if missing_html:
        preview = "\n".join(f"  {path}" for path in missing_html[:5])
        raise FileNotFoundError(
            f"{len(missing_html)} HTML source file(s) are missing under {downloads_root}:\n"
            f"{preview}\n"
            "Run `uv run data/download.py` from the repo root first."
        )
    return entries


def _filings_from_manifest(
    markdown_root: Path, downloads_root: Path, manifest_path: Path
) -> list[Filing]:
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    filings: list[Filing] = []
    for entry in payload.get("filings", []):
        status = entry.get("status")
        if status not in {None, "converted", "skipped"}:
            continue
        relative = entry.get("markdown_path")
        if not relative:
            continue
        markdown_path = markdown_root / Path(relative)
        filings.append(
            filing_from_manifest_entry(
                entry,
                markdown_path=markdown_path,
                downloads_root=downloads_root,
            )
        )
    return filings


def filing_from_manifest_entry(
    entry: dict,
    *,
    markdown_path: Path,
    downloads_root: Path,
) -> Filing:
    ticker = str(entry["ticker"]).upper()
    filing_date = date.fromisoformat(str(entry["filing_date"])[:10])
    report_date = entry.get("report_date")
    if report_date:
        filing_year = int(str(report_date)[:4])
    else:
        filing_year = filing_date.year
    accession_number = str(entry["accession_number"])
    markdown_content = markdown_path.read_text(encoding="utf-8")
    return Filing(
        ticker=ticker,
        company_name=company_name_for(ticker),
        filing_type=str(entry.get("form") or "10-K"),
        filing_date=filing_date,
        filing_year=filing_year,
        accession_number=accession_number,
        source_url=str(entry.get("source_url") or ""),
        source_html_path=resolve_source_html_path(
            entry,
            downloads_root=downloads_root,
            markdown_path=markdown_path,
            accession_number=accession_number,
        ),
        markdown_path=markdown_path,
        markdown_content=markdown_content,
    )


def resolve_source_html_path(
    entry: dict,
    *,
    downloads_root: Path,
    markdown_path: Path,
    accession_number: str,
) -> Path:
    for key in ("source_html_path", "local_path"):
        relative = entry.get(key)
        if relative:
            candidate = downloads_root / Path(str(relative))
            if candidate.is_file():
                return candidate

    stem = markdown_path.stem
    for suffix in (".htm", ".html", ".xhtml"):
        candidate = downloads_root / markdown_path.parent.name / f"{stem}{suffix}"
        if candidate.is_file():
            return candidate

    match = _FILENAME_RE.fullmatch(markdown_path.name)
    if match is not None:
        year_dir = markdown_path.parent.name
        base = markdown_path.stem
        for suffix in (".htm", ".html", ".xhtml"):
            candidate = downloads_root / year_dir / f"{base}{suffix}"
            if candidate.is_file():
                return candidate

    downloads_manifest = downloads_root / "manifest.json"
    if downloads_manifest.is_file():
        payload = json.loads(downloads_manifest.read_text(encoding="utf-8"))
        for item in payload.get("filings", []):
            if str(item.get("accession_number")) != accession_number:
                continue
            relative = item.get("local_path")
            if relative:
                candidate = downloads_root / Path(str(relative))
                if candidate.is_file():
                    return candidate

    return downloads_root / markdown_path.with_suffix(".htm").name


def _filings_from_paths(markdown_root: Path, downloads_root: Path) -> list[Filing]:
    filings: list[Filing] = []
    for path in sorted(markdown_root.rglob("*.md")):
        if path.name == "manifest.json":
            continue
        parsed = parse_markdown_filename(path, downloads_root=downloads_root)
        if parsed is None:
            continue
        filings.append(parsed)
    return filings


def parse_markdown_filename(path: Path, *, downloads_root: Path) -> Filing | None:
    match = _FILENAME_RE.fullmatch(path.name)
    if match is None:
        return None
    ticker = match.group("ticker").upper()
    filing_date = date.fromisoformat(match.group("filing_date"))
    year_from_dir = _year_from_parent(path)
    accession_number = match.group("accession")
    markdown_content = path.read_text(encoding="utf-8")
    entry = {"accession_number": accession_number}
    return Filing(
        ticker=ticker,
        company_name=company_name_for(ticker),
        filing_type="10-K",
        filing_date=filing_date,
        filing_year=year_from_dir or filing_date.year,
        accession_number=accession_number,
        source_url="",
        source_html_path=resolve_source_html_path(
            entry,
            downloads_root=downloads_root,
            markdown_path=path,
            accession_number=accession_number,
        ),
        markdown_path=path,
        markdown_content=markdown_content,
    )


def company_name_for(ticker: str) -> str:
    key = ticker.upper()
    return COMPANY_NAMES.get(key, key)


def _year_from_parent(path: Path) -> int | None:
    name = path.parent.name
    if name.isdigit() and len(name) == 4:
        return int(name)
    return None
