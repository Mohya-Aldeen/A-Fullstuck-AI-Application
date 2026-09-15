"""OpenAI embedding helpers shared by retrieval and ingestion."""

from __future__ import annotations

from openai import AsyncOpenAI

from app.config import settings

DEFAULT_BATCH_SIZE = 64


def embedding_client() -> AsyncOpenAI:
    return AsyncOpenAI(api_key=settings.OPENAI_API_KEY)


async def embed_query(client: AsyncOpenAI, query: str) -> list[float]:
    """Embed a single search query using the configured model and dimensions."""
    normalized = query.strip()
    if not normalized:
        raise ValueError("Query must not be empty")
    vectors = await embed_texts(client, [normalized])
    return vectors[0]


async def embed_texts(
    client: AsyncOpenAI,
    texts: list[str],
    *,
    batch_size: int = DEFAULT_BATCH_SIZE,
) -> list[list[float]]:
    if not texts:
        return []

    vectors: list[list[float]] = []
    model = settings.OPENAI_EMBEDDING_MODEL
    dimensions = settings.OPENAI_EMBEDDING_DIMENSIONS
    for start in range(0, len(texts), batch_size):
        batch = texts[start : start + batch_size]
        response = await client.embeddings.create(
            model=model,
            input=batch,
            dimensions=dimensions,
        )
        ordered = sorted(response.data, key=lambda item: item.index)
        batch_vectors = [item.embedding for item in ordered]
        for vector in batch_vectors:
            if len(vector) != dimensions:
                raise RuntimeError(
                    f"Embedding has {len(vector)} dimensions; expected {dimensions}"
                )
        vectors.extend(batch_vectors)
    if len(vectors) != len(texts):
        raise RuntimeError(
            f"Embedding count mismatch: expected {len(texts)}, got {len(vectors)}"
        )
    return vectors
