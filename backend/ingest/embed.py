"""Ingestion entrypoint for embedding batches (see app.embeddings)."""

from app.embeddings import DEFAULT_BATCH_SIZE, embed_texts, embedding_client

__all__ = ["DEFAULT_BATCH_SIZE", "embed_texts", "embedding_client"]
