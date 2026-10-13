"""Turn model citations into verbatim filing excerpts.

SEC table chunks are stored as cells (`iPhone, 28 = 200,583`). The model often
shortens those with ellipses or trims a sentence, which used to fail the turn.
Repair keeps a citation only when the excerpt can be replaced by passage text.
"""

from __future__ import annotations

import re

from app.assistant.outputs import Citation, GroundedAnswer
from app.assistant.registry import RetrievedPassageRegistry
from app.grounding.validator import _normalize_text
from app.retrieval.models import SourcePassage

_COMMA_NUMBER = re.compile(r"\d{1,3}(?:,\d{3})+")
_ELLIPSIS = re.compile(r"\s*(?:\.{3}|…|\.(?:\s*\.){2,})\s*")
_MARKER = re.compile(r"\[(\d+)\]")
_MAX_NUMBERS = 4
_MAX_OCCURRENCES = 6
_MAX_SPAN = 600
_MIN_FRAGMENT = 24


def repair_answer(
    answer: GroundedAnswer,
    registry: RetrievedPassageRegistry,
) -> GroundedAnswer:
    """Replace shortened excerpts with passage text, or drop ones that cannot be."""
    if answer.insufficient_evidence or not answer.citations:
        return answer

    kept: list[tuple[Citation, int]] = []
    for citation in answer.citations:
        repaired = _repair_citation(citation, registry)
        if repaired is not None:
            kept.append((repaired, citation.citation_index + 1))
    if not kept:
        return answer

    mapping = {
        old_number: new_index + 1 for new_index, (_, old_number) in enumerate(kept)
    }
    citations = [
        citation.model_copy(update={"citation_index": new_index})
        for new_index, (citation, _) in enumerate(kept)
    ]
    text = _remap_markers(answer.answer, mapping)
    if (
        len(citations) == len(answer.citations)
        and text == answer.answer
        and all(
            new == old for new, old in zip(citations, answer.citations, strict=True)
        )
    ):
        return answer
    return answer.model_copy(update={"answer": text, "citations": citations})


def example_cells(
    registry: RetrievedPassageRegistry,
    text: str,
    *,
    limit: int = 2,
) -> list[str]:
    """Verbatim cells that contain figures the model already tried to cite."""
    numbers = _comma_numbers(text)
    if not numbers:
        return []
    found: list[str] = []
    for passage in registry.all_passages():
        normalized = _normalize_text(passage.text)
        for number in numbers:
            index = normalized.find(number)
            if index < 0:
                continue
            cell = _cell_text(normalized, index, index + len(number))
            if cell not in found:
                found.append(cell)
            if len(found) >= limit:
                return found
    return found


def _repair_citation(
    citation: Citation,
    registry: RetrievedPassageRegistry,
) -> Citation | None:
    cited = registry.get(citation.chunk_id)
    if cited is not None and _contains(cited.text, citation.excerpt):
        return citation

    for passage in registry.all_passages():
        if _contains(passage.text, citation.excerpt):
            return _rebind(citation, passage, citation.excerpt)

    numbers = _comma_numbers(citation.excerpt)
    fragments = _fragments(citation.excerpt)
    chosen = _best_passage(citation, registry, numbers, fragments)
    if chosen is None:
        return None
    passage, excerpt = chosen
    return _rebind(citation, passage, excerpt)


def _best_passage(
    citation: Citation,
    registry: RetrievedPassageRegistry,
    numbers: list[str],
    fragments: list[str],
) -> tuple[SourcePassage, str] | None:
    cited = registry.get(citation.chunk_id)
    ordered: list[SourcePassage] = []
    if cited is not None:
        ordered.append(cited)
    ordered.extend(
        passage
        for passage in registry.all_passages()
        if cited is None or passage.chunk_id != cited.chunk_id
    )

    best: tuple[SourcePassage, str] | None = None
    for passage in ordered:
        excerpt = _excerpt_for(passage.text, numbers, fragments)
        if excerpt is None:
            continue
        if cited is not None and passage.chunk_id == cited.chunk_id:
            return passage, excerpt
        if best is None or len(excerpt) < len(best[1]):
            best = (passage, excerpt)
    return best


def _excerpt_for(text: str, numbers: list[str], fragments: list[str]) -> str | None:
    passage = _normalize_text(text)
    if numbers:
        spans = _tight_spans(passage, numbers)
        if spans is not None:
            return _cover(passage, spans)
    for fragment in sorted(fragments, key=len, reverse=True):
        if len(fragment) < _MIN_FRAGMENT:
            continue
        index = passage.find(fragment)
        if index < 0:
            continue
        return _sentence(passage, index, index + len(fragment))
    return None


def _cover(passage: str, spans: list[tuple[int, int]]) -> str:
    cells = [_cell_bounds(passage, start, end) for start, end in spans]
    start = min(cell[0] for cell in cells)
    end = max(cell[1] for cell in cells)
    if end - start <= _MAX_SPAN:
        return passage[start:end].strip()
    longest = max(spans, key=lambda span: span[1] - span[0])
    cell_start, cell_end = _cell_bounds(passage, longest[0], longest[1])
    return passage[cell_start:cell_end].strip()


def _cell_text(passage: str, start: int, end: int) -> str:
    cell_start, cell_end = _cell_bounds(passage, start, end)
    return passage[cell_start:cell_end].strip()


def _cell_bounds(passage: str, start: int, end: int) -> tuple[int, int]:
    left_dot = passage.rfind(". ", 0, start)
    left_break = passage.rfind("\n", 0, start)
    left = max(left_dot, left_break)
    cell_start = 0 if left < 0 else left + (2 if left == left_dot else 1)
    right_dot = passage.find(". ", end)
    right_break = passage.find("\n", end)
    rights = [index for index in (right_dot, right_break) if index >= 0]
    if not rights:
        return cell_start, len(passage)
    right = min(rights)
    if right == right_dot:
        return cell_start, right
    return cell_start, right


def _sentence(passage: str, start: int, end: int) -> str:
    left_dot = passage.rfind(". ", 0, start)
    begin = 0 if left_dot < 0 else left_dot + 2
    colon = passage.find(":", end, end + 160)
    period = passage.find(". ", end)
    if colon >= 0 and (period < 0 or colon <= period):
        finish = colon + 1
    elif period >= 0:
        finish = period + 1
    else:
        finish = min(len(passage), end + 80)
    sentence = passage[begin:finish].strip()
    if len(sentence) > 400:
        return passage[start:end]
    return sentence


def _tight_spans(passage: str, numbers: list[str]) -> list[tuple[int, int]] | None:
    positions: list[list[tuple[int, int]]] = []
    for number in numbers[:_MAX_NUMBERS]:
        found: list[tuple[int, int]] = []
        cursor = 0
        while len(found) < _MAX_OCCURRENCES:
            index = passage.find(number, cursor)
            if index < 0:
                break
            found.append((index, index + len(number)))
            cursor = index + 1
        if not found:
            return None
        positions.append(found)

    best: tuple[int, list[tuple[int, int]]] | None = None

    def walk(index: int, chosen: list[tuple[int, int]]) -> None:
        nonlocal best
        if index == len(positions):
            span = max(end for _, end in chosen) - min(start for start, _ in chosen)
            if best is None or span < best[0]:
                best = (span, list(chosen))
            return
        for position in positions[index]:
            walk(index + 1, chosen + [position])

    walk(0, [])
    if best is None:
        return None
    return best[1]


def _contains(passage_text: str, excerpt: str) -> bool:
    return _normalize_text(excerpt) in _normalize_text(passage_text)


def _rebind(citation: Citation, passage: SourcePassage, excerpt: str) -> Citation:
    if (
        citation.chunk_id == passage.chunk_id
        and citation.excerpt == excerpt
        and citation.page_label
    ):
        return citation
    return citation.model_copy(
        update={
            "chunk_id": passage.chunk_id,
            "excerpt": excerpt,
            "page_label": citation.page_label or passage.page_label,
        }
    )


def _comma_numbers(text: str) -> list[str]:
    seen: list[str] = []
    for number in _COMMA_NUMBER.findall(text):
        if number not in seen:
            seen.append(number)
    return seen


def _fragments(excerpt: str) -> list[str]:
    parts = [_normalize_text(part) for part in _ELLIPSIS.split(excerpt)]
    return [part for part in parts if part]


def _remap_markers(answer: str, mapping: dict[int, int]) -> str:
    def replace(match: re.Match[str]) -> str:
        new_number = mapping.get(int(match.group(1)))
        if new_number is None:
            return ""
        return f"[{new_number}]"

    text = _MARKER.sub(replace, answer)
    text = re.sub(r"[ \t]{2,}", " ", text)
    text = re.sub(r" +([.,;:])", r"\1", text)
    return text.strip()
