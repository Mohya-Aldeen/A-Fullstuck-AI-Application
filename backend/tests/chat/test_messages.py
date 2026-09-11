from uuid import uuid4

import pytest
from pydantic_ai.ui.vercel_ai.request_types import TextUIPart, UIMessage

from app.chat.messages import (
    build_assistant_ui_message,
    extract_last_user_message,
    message_text,
    parse_stream_request,
    title_from_first_message,
)


def _user_message(text: str) -> UIMessage:
    return UIMessage(
        id=str(uuid4()),
        role="user",
        parts=[TextUIPart(text=text)],
    )


def test_parse_stream_request_accepts_thread_id_alias() -> None:
    thread_id = uuid4()
    request = parse_stream_request(
        {
            "threadId": str(thread_id),
            "messages": [
                {
                    "id": "msg-1",
                    "role": "user",
                    "parts": [{"type": "text", "text": "Hello"}],
                }
            ],
        }
    )
    assert request.thread_id == thread_id
    assert len(request.messages) == 1


def test_extract_last_user_message_skips_trailing_assistant() -> None:
    messages = [
        _user_message("first"),
        UIMessage(
            id=str(uuid4()),
            role="assistant",
            parts=[TextUIPart(text="reply")],
        ),
        _user_message("second"),
    ]
    last = extract_last_user_message(messages)
    assert last is not None
    assert message_text(last) == "second"


def test_message_text_joins_multiple_text_parts() -> None:
    message = UIMessage(
        id=str(uuid4()),
        role="user",
        parts=[TextUIPart(text=" line one "), TextUIPart(text="line two")],
    )
    assert message_text(message) == "line one\nline two"


def test_title_from_first_message_truncates_long_text() -> None:
    title = title_from_first_message("a" * 80, max_len=10)
    assert len(title) == 10
    assert title.endswith("…")


def test_build_assistant_ui_message_includes_text_part() -> None:
    ui_message = build_assistant_ui_message(text="Done", message_id="assistant-1")
    assert ui_message["id"] == "assistant-1"
    assert ui_message["role"] == "assistant"
    assert ui_message["parts"][0]["text"] == "Done"


def test_parse_stream_request_rejects_missing_thread_id() -> None:
    with pytest.raises(ValueError):
        parse_stream_request({"messages": []})
