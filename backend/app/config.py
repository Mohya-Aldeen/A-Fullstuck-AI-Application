"""
Single source of truth for backend configuration.

Per AGENTS.md: no os.getenv or load_dotenv anywhere else in the app.
Import `settings` wherever config is needed:

    from app.config import settings
    settings.OPENAI_API_KEY
"""

from typing import List

from pydantic import AnyHttpUrl, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # --- Supabase (Auth + API) ---
    SUPABASE_URL: AnyHttpUrl
    SUPABASE_ANON_KEY: str
    SUPABASE_SERVICE_ROLE_KEY: str

    # --- Postgres (SQLAlchemy models + Alembic migrations) ---
    DATABASE_URL: str

    # --- OpenAI (LLM + embeddings) ---
    OPENAI_API_KEY: str
    OPENAI_EMBEDDING_MODEL: str = "text-embedding-3-small"
    OPENAI_EMBEDDING_DIMENSIONS: int = 1536

    # --- Server ---
    ALLOWED_ORIGINS: List[str] = ["http://localhost:5173"]

    @field_validator("ALLOWED_ORIGINS", mode="before")
    @classmethod
    def split_origins(cls, v: str | List[str]) -> List[str]:
        """ALLOWED_ORIGINS is a comma-separated string in .env."""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v


# Instantiated once at import time — missing/invalid required vars raise
# immediately on startup rather than failing later at first use.
settings = Settings()
