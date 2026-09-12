"""Chunk SEC HTML filings with Docling HybridChunker (hierarchical + token-aware)."""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

import tiktoken
from docling.chunking import HybridChunker
from docling.datamodel.base_models import ConversionStatus
from docling.document_converter import DocumentConverter
from docling_core.transforms.chunker.tokenizer.openai import OpenAITokenizer

from app.config import settings

SMOKE_TEST_ACCESSION = "0000320193-21-000105"
SMOKE_TEST_NEEDLES = ("191,973", "iPhone")


@dataclass(frozen=True)
class PreparedChunk:
    index: int
    text: str
    embedding_text: str
    token_count: int
    page_label: str | None
    section_label: str | None
    headings: tuple[str, ...]


class SecOpenAITokenizer(OpenAITokenizer):
    """SEC HTML can contain bytes that trip tiktoken's default special-token guard."""

    def count_tokens(self, text: str) -> int:
        return len(
            self.tokenizer.encode(text, disallowed_special=())
        )


@lru_cache(maxsize=1)
def _converter() -> DocumentConverter:
    return DocumentConverter()


@lru_cache(maxsize=1)
def _chunker() -> HybridChunker:
    encoding = tiktoken.encoding_for_model(settings.OPENAI_EMBEDDING_MODEL)
    tokenizer = SecOpenAITokenizer(
        tokenizer=encoding,
        max_tokens=settings.INGEST_CHUNK_MAX_TOKENS,
    )
    return HybridChunker(
        tokenizer=tokenizer,
        merge_peers=True,
        repeat_table_header=True,
    )


def convert_html_to_docling(html_path: Path):
    result = _converter().convert(html_path)
    if result.status != ConversionStatus.SUCCESS:
        raise RuntimeError(
            f"Docling conversion failed for {html_path} with status {result.status!s}"
        )
    if result.document is None:
        raise RuntimeError(f"Docling returned no document for {html_path}")
    return result.document


def extract_section_label(chunk) -> str | None:
    meta = getattr(chunk, "meta", None)
    if meta is None:
        return None
    headings = getattr(meta, "headings", None) or []
    labels = [str(item).strip() for item in headings if str(item).strip()]
    if not labels:
        return None
    return " > ".join(labels)


def extract_page_label(chunk) -> str | None:
    meta = getattr(chunk, "meta", None)
    if meta is None:
        return None
    for item in getattr(meta, "doc_items", None) or []:
        for prov in getattr(item, "prov", None) or []:
            page_no = getattr(prov, "page_no", None)
            if page_no is not None:
                return str(int(page_no) + 1)
    return None


def extract_headings(chunk) -> tuple[str, ...]:
    meta = getattr(chunk, "meta", None)
    if meta is None:
        return ()
    headings = getattr(meta, "headings", None) or []
    return tuple(str(item).strip() for item in headings if str(item).strip())


def chunk_html_path(html_path: Path) -> list[PreparedChunk]:
    document = convert_html_to_docling(html_path)
    chunker = _chunker()
    prepared: list[PreparedChunk] = []
    for index, chunk in enumerate(chunker.chunk(dl_doc=document)):
        text = chunk.text.strip()
        if not text:
            continue
        embedding_text = chunker.contextualize(chunk=chunk).strip()
        if not embedding_text:
            continue
        prepared.append(
            PreparedChunk(
                index=index,
                text=text,
                embedding_text=embedding_text,
                token_count=max(1, chunker.tokenizer.count_tokens(embedding_text)),
                page_label=extract_page_label(chunk),
                section_label=extract_section_label(chunk),
                headings=extract_headings(chunk),
            )
        )
    if not prepared:
        raise RuntimeError(f"No chunks produced for {html_path}")
    return prepared


def find_smoke_test_chunk(
    chunks: list[PreparedChunk],
    *,
    needles: tuple[str, ...] = SMOKE_TEST_NEEDLES,
) -> PreparedChunk:
    for chunk in chunks:
        haystack = f"{chunk.text}\n{chunk.embedding_text}"
        if all(needle in haystack for needle in needles):
            return chunk
    preview = "\n".join(f"  [{c.index}] {c.section_label}" for c in chunks[:8])
    raise RuntimeError(
        f"No chunk matched smoke-test needles {needles!r}. First chunks:\n{preview}"
    )
