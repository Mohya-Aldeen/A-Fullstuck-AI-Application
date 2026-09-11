"""AI SDK UI message parsing and persistence helpers."""

from __future__ import annotations

from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field, ValidationError
from pydantic_ai.ui.vercel_ai.request_types import TextUIPart, UIMessage

STUB_ASSISTANT_REPLY = (
    "Document Copilot is connected. Retrieval and the grounded assistant are not wired yet — "
    "this is a stub response from the backend."
)


class StreamChatRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    thread_id: UUID = Field(alias="threadId")
    messages: list[UIMessage]


def parse_stream_request(body: dict) -> StreamChatRequest:
    try:
        return StreamChatRequest.model_validate(body)
    except ValidationError as exc:
        raise ValueError(str(exc)) from exc


def extract_last_user_message(messages: list[UIMessage]) -> UIMessage | None:
    for message in reversed(messages):
        if message.role == "user":
            return message
    return None


def message_text(message: UIMessage) -> str:
    parts: list[str] = []
    for part in message.parts:
        if isinstance(part, TextUIPart):
            text = part.text.strip()
            if text:
                parts.append(text)
    return "\n".join(parts)


def ui_message_to_dict(message: UIMessage) -> dict:
    return message.model_dump(mode="json", by_alias=True)


def build_assistant_ui_message(*, text: str, message_id: str | None = None) -> dict:
    msg_id = message_id or str(uuid4())
    return {
        "id": msg_id,
        "role": "assistant",
        "parts": [{"type": "text", "text": text, "state": "done"}],
    }


def title_from_first_message(text: str, *, max_len: int = 60) -> str:
    collapsed = " ".join(text.split())
    if not collapsed:
        return "New chat"
    if len(collapsed) <= max_len:
        return collapsed
    return collapsed[: max_len - 1].rstrip() + "…"
