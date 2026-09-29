# Phase 7 — Chat API and streaming

## Purpose

Expose the assistant over HTTP so the React app can list chats, send a question, and show the answer as it arrives.

Most routes are ordinary JSON. The answer itself is a stream, because waiting for a full grounded answer before showing anything feels broken.

## Routes

All chat routes require the bearer token from Phase 3.

| Method | Path | Returns |
| ------ | ---- | ------- |
| GET | `/health` | `{status: ok}` — public |
| GET | `/me` | Current user id and email |
| GET | `/chat/threads` | This user's threads |
| POST | `/chat/threads` | Creates a thread |
| GET | `/chat/threads/{id}/messages` | History, including citations saved earlier |
| POST | `/chat/stream` | The assistant turn as a server-sent event stream |

`app/chat/messages.py` converts between the Vercel AI SDK UI message shape and the rows we store. `app/chat/streaming.py` writes the event stream that `@ai-sdk/react` `useChat` already understands. The frontend does not invent a second protocol.

Error codes used on purpose:

| Code | Meaning |
| ---- | ------- |
| 401 | Not signed in |
| 403 | Thread belongs to someone else |
| 404 | Thread does not exist |
| 422 | The body is not a valid chat request |
| 502 | Retrieval, database, or the model failed |

## What is still open

There is no `@pytest.mark.integration` test that runs a full live chat against Supabase and OpenAI. The unit tests mock the agent. A live test spends API money and needs real credentials, so it was left out of the default suite.

## How to check it

Start the backend, sign in through the frontend, create a thread, and send a question. Reload the thread. The answer and its citations should still be there, which proves the persist step ran.
