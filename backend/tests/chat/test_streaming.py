import asyncio

from app.chat.streaming import stream_assistant_text


def test_stream_assistant_text_emits_vercel_ai_events() -> None:
    async def collect() -> list[str]:
        events: list[str] = []
        async for event in stream_assistant_text("Hello world", message_id="msg-1"):
            events.append(event)
        return events

    joined = "".join(asyncio.run(collect()))
    assert "data: " in joined
    assert '"type":"start"' in joined or '"type": "start"' in joined
    assert "text-delta" in joined
    assert "data: [DONE]" in joined
