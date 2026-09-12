from dataclasses import dataclass
from pathlib import Path

import pytest

from ingest.docling_chunking import (
    PreparedChunk,
    extract_page_label,
    extract_section_label,
    find_smoke_test_chunk,
)


@dataclass
class _Prov:
    page_no: int


@dataclass
class _Item:
    prov: list[_Prov]


@dataclass
class _Meta:
    headings: list[str]
    doc_items: list[_Item]


@dataclass
class _Chunk:
    meta: _Meta
    text: str = "body"


def test_extract_section_label_joins_headings() -> None:
    chunk = _Chunk(meta=_Meta(headings=["Item 7.", "Products and Services"], doc_items=[]))
    assert extract_section_label(chunk) == "Item 7. > Products and Services"


def test_extract_page_label_from_provenance() -> None:
    chunk = _Chunk(
        meta=_Meta(headings=[], doc_items=[_Item(prov=[_Prov(page_no=19)])]),
    )
    assert extract_page_label(chunk) == "20"


def test_find_smoke_test_chunk() -> None:
    chunks = [
        PreparedChunk(
            index=0,
            text="unrelated",
            embedding_text="unrelated",
            token_count=1,
            page_label=None,
            section_label=None,
            headings=(),
        ),
        PreparedChunk(
            index=1,
            text="iPhone net sales were $191,973 million",
            embedding_text="Item 7.\niPhone net sales were $191,973 million",
            token_count=10,
            page_label="20",
            section_label="Item 7.",
            headings=("Item 7.",),
        ),
    ]
    selected = find_smoke_test_chunk(chunks)
    assert selected.index == 1


def test_find_smoke_test_chunk_raises_when_missing() -> None:
    chunks = [
        PreparedChunk(
            index=0,
            text="no match",
            embedding_text="no match",
            token_count=1,
            page_label=None,
            section_label=None,
            headings=(),
        )
    ]
    with pytest.raises(RuntimeError, match="No chunk matched smoke-test needles"):
        find_smoke_test_chunk(chunks)


@pytest.mark.integration
def test_chunk_apple_2021_html_produces_revenue_passage() -> None:
    repo_root = Path(__file__).resolve().parents[3]
    html = (
        repo_root
        / "data"
        / "downloads"
        / "2021"
        / "aapl_10-k_2021-10-29_0000320193-21-000105.htm"
    )
    if not html.is_file():
        pytest.skip("local HTML corpus not present")

    from ingest.docling_chunking import chunk_html_path

    chunks = chunk_html_path(html)
    assert len(chunks) > 20
    selected = find_smoke_test_chunk(chunks)
    assert "191,973" in selected.text or "191,973" in selected.embedding_text
    assert "iPhone" in selected.text or "iPhone" in selected.embedding_text
