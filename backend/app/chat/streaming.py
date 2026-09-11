"""AI SDK-compatible SSE streaming for assistant turns."""

from __future__ import annotations

from collections.abc import AsyncIterator
from uuid import uuid4

from pydantic_ai.ui.vercel_ai.response_types import (
    DoneChunk,
    FinishChunk,
    FinishStepChunk,
    StartChunk,
    StartStepChunk,
    TextDeltaChunk,
    TextEndChunk,
    TextStartChunk,
)

VERCEL_AI_STREAM_HEADERS = {"x-vercel-ai-ui-message-stream": "v1"}
SDK_VERSION = 6


def _encode(chunk) -> str:
    return f"data: {chunk.encode(SDK_VERSION)}\n\n"


def _chunk_text(text: str, *, size: int = 24) -> list[str]:
    words = text.split(" ")
    chunks: list[str] = []
    current = ""
    for word in words:
        piece = word if not current else f"{current} {word}"
        if len(piece) > size and current:
            chunks.append(current + " ")
            current = word
        else:
            current = piece
    if current:
        chunks.append(current)
    return chunks or [text]


async def stream_assistant_text(text: str, *, message_id: str | None = None) -> AsyncIterator[str]:
    """Emit a minimal Vercel AI UI message stream for plain assistant text."""
    assistant_message_id = message_id or str(uuid4())
    text_part_id = str(uuid4())

    yield _encode(StartChunk(message_id=assistant_message_id))
    yield _encode(StartStepChunk())
    yield _encode(TextStartChunk(id=text_part_id))

    for delta in _chunk_text(text):
        yield _encode(TextDeltaChunk(id=text_part_id, delta=delta))

    yield _encode(TextEndChunk(id=text_part_id))
    yield _encode(FinishStepChunk())
    yield _encode(FinishChunk(finish_reason="stop"))
    yield _encode(DoneChunk())
