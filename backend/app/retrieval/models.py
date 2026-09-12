"""Small immutable types shared by the retrieval pipeline."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from uuid import UUID


@dataclass(frozen=True)
class SearchFilters:
    tickers: tuple[str, ...] = ()
    filing_types: tuple[str, ...] = ()
    start_year: int | None = None
    end_year: int | None = None

    def rpc_params(self) -> dict[str, object]:
        return {
            "filter_tickers": list(self.tickers) or None,
            "filter_filing_types": list(self.filing_types) or None,
            "filter_start_year": self.start_year,
            "filter_end_year": self.end_year,
        }


@dataclass(frozen=True)
class RankedChunk:
    chunk_id: UUID
    score: float


@dataclass(frozen=True)
class FusedChunk:
    chunk_id: UUID
    rrf_score: float
    semantic_rank: int | None
    lexical_rank: int | None


@dataclass(frozen=True)
class FilingMetadata:
    document_id: UUID
    ticker: str
    company_name: str
    filing_type: str
    filing_date: date
    filing_year: int
    accession_number: str
    source_url: str


@dataclass(frozen=True)
class ChunkRecord:
    chunk_id: UUID
    document_id: UUID
    chunk_index: int
    text: str
    token_count: int
    page_label: str | None
    section_label: str | None
    chunk_metadata: dict = field(default_factory=dict)
    filing: FilingMetadata | None = None


@dataclass(frozen=True)
class SourcePassage:
    chunk_id: UUID
    document_id: UUID
    chunk_index: int
    text: str
    token_count: int
    page_label: str | None
    section_label: str | None
    ticker: str
    company_name: str
    filing_type: str
    filing_date: date
    filing_year: int
    accession_number: str
    source_url: str
    rrf_score: float | None = None
    semantic_rank: int | None = None
    lexical_rank: int | None = None


def passage_from_chunk(
    chunk: ChunkRecord,
    *,
    fused: FusedChunk | None = None,
) -> SourcePassage:
    if chunk.filing is None:
        raise ValueError(f"Chunk {chunk.chunk_id} has no filing metadata")
    return SourcePassage(
        chunk_id=chunk.chunk_id,
        document_id=chunk.document_id,
        chunk_index=chunk.chunk_index,
        text=chunk.text,
        token_count=chunk.token_count,
        page_label=chunk.page_label,
        section_label=chunk.section_label,
        ticker=chunk.filing.ticker,
        company_name=chunk.filing.company_name,
        filing_type=chunk.filing.filing_type,
        filing_date=chunk.filing.filing_date,
        filing_year=chunk.filing.filing_year,
        accession_number=chunk.filing.accession_number,
        source_url=chunk.filing.source_url,
        rrf_score=fused.rrf_score if fused is not None else None,
        semantic_rank=fused.semantic_rank if fused is not None else None,
        lexical_rank=fused.lexical_rank if fused is not None else None,
    )
