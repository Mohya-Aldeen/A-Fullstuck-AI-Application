"""Runtime dependencies for the document assistant agent."""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from openai import AsyncOpenAI
from supabase import AsyncClient

from app.assistant.registry import RetrievedPassageRegistry
from app.assistant.tools_adapter import InstrumentedRetrievalTools
from app.embeddings import embedding_client
from app.grounding.validator import GroundingValidator
from app.retrieval.retriever import DocumentRetriever


@dataclass
class DocumentAgentDeps:
    user_id: UUID
    thread_id: UUID
    tools: InstrumentedRetrievalTools
    registry: RetrievedPassageRegistry
    validator: GroundingValidator


def build_agent_deps(
    *,
    user_id: UUID,
    thread_id: UUID,
    supabase: AsyncClient,
    openai_client: AsyncOpenAI | None = None,
) -> DocumentAgentDeps:
    registry = RetrievedPassageRegistry()
    retriever = DocumentRetriever(
        supabase,
        openai_client or embedding_client(),
    )
    return DocumentAgentDeps(
        user_id=user_id,
        thread_id=thread_id,
        tools=InstrumentedRetrievalTools(retriever=retriever, registry=registry),
        registry=registry,
        validator=GroundingValidator(),
    )
