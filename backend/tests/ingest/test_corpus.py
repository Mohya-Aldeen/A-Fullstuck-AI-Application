from datetime import date
from pathlib import Path

from ingest.corpus import (
    company_name_for,
    filing_from_manifest_entry,
    load_filings,
    parse_markdown_filename,
    resolve_source_html_path,
)


def test_resolve_source_html_path_from_manifest_fields(tmp_path: Path) -> None:
    downloads = tmp_path / "downloads"
    markdown = tmp_path / "markdown"
    html = downloads / "2021" / "aapl_10-k_2021-10-29_0000320193-21-000105.htm"
    md = markdown / "2021" / "aapl_10-k_2021-10-29_0000320193-21-000105.md"
    html.parent.mkdir(parents=True)
    md.parent.mkdir(parents=True)
    html.write_text("<html></html>", encoding="utf-8")
    md.write_text("markdown body", encoding="utf-8")

    resolved = resolve_source_html_path(
        {
            "source_html_path": "2021/aapl_10-k_2021-10-29_0000320193-21-000105.htm",
            "local_path": "2021\\aapl_10-k_2021-10-29_0000320193-21-000105.htm",
        },
        downloads_root=downloads,
        markdown_path=md,
        accession_number="0000320193-21-000105",
    )
    assert resolved == html


def test_filing_from_manifest_includes_html_and_markdown(tmp_path: Path) -> None:
    downloads = tmp_path / "downloads"
    markdown = tmp_path / "markdown"
    html = downloads / "2021" / "aapl_10-k_2021-10-29_0000320193-21-000105.htm"
    md = markdown / "2021" / "aapl_10-k_2021-10-29_0000320193-21-000105.md"
    html.parent.mkdir(parents=True)
    md.parent.mkdir(parents=True)
    html.write_text("<html></html>", encoding="utf-8")
    md.write_text("markdown body", encoding="utf-8")

    filing = filing_from_manifest_entry(
        {
            "ticker": "AAPL",
            "form": "10-K",
            "filing_date": "2022-10-28",
            "report_date": "2021-09-25",
            "accession_number": "0000320193-21-000105",
            "source_url": "https://www.sec.gov/example",
            "source_html_path": "2021/aapl_10-k_2021-10-29_0000320193-21-000105.htm",
        },
        markdown_path=md,
        downloads_root=downloads,
    )
    assert filing.filing_year == 2021
    assert filing.source_html_path == html
    assert filing.markdown_content == "markdown body"


def test_parse_markdown_filename(tmp_path: Path) -> None:
    downloads = tmp_path / "downloads"
    path = tmp_path / "2021" / "aapl_10-k_2021-10-29_0000320193-21-000105.md"
    html = downloads / "2021" / "aapl_10-k_2021-10-29_0000320193-21-000105.htm"
    path.parent.mkdir()
    html.parent.mkdir(parents=True)
    path.write_text("Apple Inc. filing body", encoding="utf-8")
    html.write_text("<html></html>", encoding="utf-8")

    filing = parse_markdown_filename(path, downloads_root=downloads)
    assert filing is not None
    assert filing.ticker == "AAPL"
    assert filing.accession_number == "0000320193-21-000105"
    assert filing.source_html_path == html


def test_company_name_for_known_and_unknown_tickers() -> None:
    assert company_name_for("googl") == "Alphabet Inc."
    assert company_name_for("XYZ") == "XYZ"


def test_load_filings_filters_by_accession() -> None:
    repo_root = Path(__file__).resolve().parents[3]
    markdown_dir = repo_root / "data" / "markdown"
    downloads_dir = repo_root / "data" / "downloads"
    if not markdown_dir.is_dir() or not downloads_dir.is_dir():
        return

    filings = load_filings(
        markdown_dir,
        downloads_dir,
        accession_number="0000320193-21-000105",
    )
    assert len(filings) == 1
    assert filings[0].ticker == "AAPL"
    assert filings[0].filing_date == date(2021, 10, 29)
