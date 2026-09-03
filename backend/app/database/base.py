"""SQLAlchemy base metadata for the application.

Keep this file minimal — Alembic imports `Base.metadata` from here for
autogenerate support.
"""

from sqlalchemy.orm import declarative_base

Base = declarative_base()

__all__ = ["Base"]
