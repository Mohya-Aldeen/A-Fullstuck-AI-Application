"""
Single source of truth for backend configuration.

Per AGENTS.md: no os.getenv or load_dotenv anywhere else in the app.
Import `settings` wherever config is needed:

    from app.config import settings
    settings.OPENAI_API_KEY
"""

from pydantic import computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # --- Supabase (Auth + API) ---
    SUPABASE_URL: str
    SUPABASE_ANON_KEY: str
    SUPABASE_SERVICE_ROLE_KEY: str

    # --- Postgres (SQLAlchemy models + Alembic migrations) ---
    DATABASE_URL: str

    # --- OpenAI (LLM + embeddings) ---
    OPENAI_API_KEY: str
    OPENAI_EMBEDDING_MODEL: str = "text-embedding-3-small"
    OPENAI_EMBEDDING_DIMENSIONS: int = 1536
    # Docling HybridChunker token budget (aligned to OpenAI embedding tokenizer).
    INGEST_CHUNK_MAX_TOKENS: int = 512

    # --- Server ---
    # Comma-separated in .env (see .env.example). Stored as str so pydantic-settings
    # does not try to JSON-decode the value before our split runs.
    ALLOWED_ORIGINS: str = "http://localhost:5173"

    @computed_field
    @property
    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",") if origin.strip()]


# Instantiated once at import time — missing/invalid required vars raise
# immediately on startup rather than failing later at first use.
settings = Settings()
