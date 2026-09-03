from __future__ import with_statement

import os
import sys
from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool

from alembic import context

# Ensure project root is on path so app imports work
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Import settings and metadata from the app
try:
    from app.config import settings
    from app.database.base import Base
except Exception as exc:  # pragma: no cover - fail fast at runtime with helpful message
    raise RuntimeError(
        "Failed importing application settings or metadata. Ensure backend/.env is populated before running migrations."
    ) from exc

config = context.config

# Interpret the config file for Python logging.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    url = settings.DATABASE_URL
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    configuration = {"sqlalchemy.url": settings.DATABASE_URL}
    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
