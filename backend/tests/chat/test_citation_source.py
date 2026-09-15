from uuid import uuid4

from app.database.chats import _citation_from_row, citation_source_from_nested_row


def test_citation_source_from_nested_row() -> None:
    row = {
        "document_chunks": {
            "page_label": "42",
            "section_label": "Item 7",
            "source_documents": {
                "ticker": "AAPL",
                "company_name": "Apple Inc.",
                "filing_type": "10-K",
                "filing_date": "2021-10-29",
                "filing_year": 2021,
                "source_url": "https://example.com/filing",
                "accession_number": "0000320193-21-000105",
            },
        }
    }
    source = citation_source_from_nested_row(row)
    assert source is not None
    assert source.ticker == "AAPL"
    assert source.section_label == "Item 7"
    assert source.filing_year == 2021


def test_citation_from_row_fills_page_from_chunk() -> None:
    message_id = uuid4()
    chunk_id = uuid4()
    citation_id = uuid4()
    row = {
        "id": str(citation_id),
        "message_id": str(message_id),
        "chunk_id": str(chunk_id),
        "citation_index": 0,
        "excerpt": "iPhone net sales were $191,973 million.",
        "page_label": None,
        "document_chunks": {
            "page_label": "21",
            "section_label": None,
            "source_documents": {
                "ticker": "AAPL",
                "company_name": "Apple Inc.",
                "filing_type": "10-K",
                "filing_date": "2021-10-29",
                "filing_year": 2021,
                "source_url": "https://example.com/filing",
                "accession_number": "0000320193-21-000105",
            },
        },
    }
    citation = _citation_from_row(row)
    assert citation.page_label == "21"
    assert citation.source is not None
    assert citation.source.ticker == "AAPL"
