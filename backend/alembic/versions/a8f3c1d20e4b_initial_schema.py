"""Initial schema: profiles, chats, documents, pgvector, full-text search, RLS.

Revision ID: a8f3c1d20e4b
Revises:
Create Date: 2026-09-03 12:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from pgvector.sqlalchemy import Vector
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "a8f3c1d20e4b"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

EMBEDDING_DIMENSIONS = 1536


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    op.create_table(
        "profiles",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("email", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.execute(
        """
        ALTER TABLE profiles
        ADD CONSTRAINT profiles_id_fkey
        FOREIGN KEY (id) REFERENCES auth.users (id) ON DELETE CASCADE
        """
    )

    op.create_table(
        "source_documents",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("ticker", sa.String(length=16), nullable=False),
        sa.Column("company_name", sa.Text(), nullable=False),
        sa.Column("filing_type", sa.String(length=32), nullable=False),
        sa.Column("filing_date", sa.Date(), nullable=False),
        sa.Column("filing_year", sa.Integer(), nullable=False),
        sa.Column("accession_number", sa.String(length=64), nullable=False),
        sa.Column("source_url", sa.Text(), nullable=False),
        sa.Column("markdown_content", sa.Text(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("accession_number"),
    )
    op.create_index("ix_source_documents_ticker", "source_documents", ["ticker"], unique=False)
    op.create_index("ix_source_documents_filing_year", "source_documents", ["filing_year"], unique=False)

    op.create_table(
        "chat_threads",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("title", sa.Text(), server_default="New chat", nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["user_id"], ["profiles.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_chat_threads_user_id", "chat_threads", ["user_id"], unique=False)

    op.create_table(
        "document_chunks",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("document_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("chunk_index", sa.Integer(), nullable=False),
        sa.Column("page_label", sa.Text(), nullable=True),
        sa.Column("section_label", sa.Text(), nullable=True),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("token_count", sa.Integer(), nullable=False),
        sa.Column(
            "chunk_metadata",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        sa.Column("embedding", Vector(EMBEDDING_DIMENSIONS), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["document_id"], ["source_documents.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("document_id", "chunk_index", name="uq_document_chunks_document_index"),
    )
    op.create_index("ix_document_chunks_document_id", "document_chunks", ["document_id"], unique=False)
    op.create_index(
        "ix_document_chunks_metadata",
        "document_chunks",
        ["chunk_metadata"],
        unique=False,
        postgresql_using="gin",
    )

    op.execute(
        """
        ALTER TABLE document_chunks
        ADD COLUMN search_vector tsvector
        GENERATED ALWAYS AS (to_tsvector('english', text)) STORED
        """
    )
    op.execute(
        """
        CREATE INDEX ix_document_chunks_search_vector
        ON document_chunks
        USING gin (search_vector)
        """
    )
    op.execute(
        """
        CREATE INDEX ix_document_chunks_embedding_hnsw
        ON document_chunks
        USING hnsw (embedding vector_cosine_ops)
        """
    )

    op.create_table(
        "chat_messages",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("thread_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("role", sa.String(length=32), nullable=False),
        sa.Column("ui_message", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("sequence", sa.Integer(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["thread_id"], ["chat_threads.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("thread_id", "sequence", name="uq_chat_messages_thread_sequence"),
    )
    op.create_index("ix_chat_messages_thread_id", "chat_messages", ["thread_id"], unique=False)

    op.create_table(
        "message_citations",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("message_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("chunk_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("citation_index", sa.Integer(), nullable=False),
        sa.Column("excerpt", sa.Text(), nullable=True),
        sa.Column("page_label", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["chunk_id"], ["document_chunks.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["message_id"], ["chat_messages.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("message_id", "citation_index", name="uq_message_citations_message_index"),
    )
    op.create_index("ix_message_citations_message_id", "message_citations", ["message_id"], unique=False)
    op.create_index("ix_message_citations_chunk_id", "message_citations", ["chunk_id"], unique=False)

    _enable_rls_and_policies()


def _enable_rls_and_policies() -> None:
    for table in (
        "profiles",
        "chat_threads",
        "chat_messages",
        "message_citations",
        "source_documents",
        "document_chunks",
    ):
        op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY")

    op.execute(
        """
        CREATE POLICY profiles_select_own
        ON profiles FOR SELECT TO authenticated
        USING (auth.uid() = id)
        """
    )
    op.execute(
        """
        CREATE POLICY profiles_update_own
        ON profiles FOR UPDATE TO authenticated
        USING (auth.uid() = id)
        WITH CHECK (auth.uid() = id)
        """
    )
    op.execute(
        """
        CREATE POLICY profiles_insert_own
        ON profiles FOR INSERT TO authenticated
        WITH CHECK (auth.uid() = id)
        """
    )

    op.execute(
        """
        CREATE POLICY chat_threads_select_own
        ON chat_threads FOR SELECT TO authenticated
        USING (auth.uid() = user_id)
        """
    )
    op.execute(
        """
        CREATE POLICY chat_threads_insert_own
        ON chat_threads FOR INSERT TO authenticated
        WITH CHECK (auth.uid() = user_id)
        """
    )
    op.execute(
        """
        CREATE POLICY chat_threads_update_own
        ON chat_threads FOR UPDATE TO authenticated
        USING (auth.uid() = user_id)
        WITH CHECK (auth.uid() = user_id)
        """
    )
    op.execute(
        """
        CREATE POLICY chat_threads_delete_own
        ON chat_threads FOR DELETE TO authenticated
        USING (auth.uid() = user_id)
        """
    )

    op.execute(
        """
        CREATE POLICY chat_messages_select_own
        ON chat_messages FOR SELECT TO authenticated
        USING (
            EXISTS (
                SELECT 1
                FROM chat_threads t
                WHERE t.id = chat_messages.thread_id
                  AND t.user_id = auth.uid()
            )
        )
        """
    )
    op.execute(
        """
        CREATE POLICY chat_messages_insert_own
        ON chat_messages FOR INSERT TO authenticated
        WITH CHECK (
            EXISTS (
                SELECT 1
                FROM chat_threads t
                WHERE t.id = chat_messages.thread_id
                  AND t.user_id = auth.uid()
            )
        )
        """
    )
    op.execute(
        """
        CREATE POLICY chat_messages_update_own
        ON chat_messages FOR UPDATE TO authenticated
        USING (
            EXISTS (
                SELECT 1
                FROM chat_threads t
                WHERE t.id = chat_messages.thread_id
                  AND t.user_id = auth.uid()
            )
        )
        WITH CHECK (
            EXISTS (
                SELECT 1
                FROM chat_threads t
                WHERE t.id = chat_messages.thread_id
                  AND t.user_id = auth.uid()
            )
        )
        """
    )
    op.execute(
        """
        CREATE POLICY chat_messages_delete_own
        ON chat_messages FOR DELETE TO authenticated
        USING (
            EXISTS (
                SELECT 1
                FROM chat_threads t
                WHERE t.id = chat_messages.thread_id
                  AND t.user_id = auth.uid()
            )
        )
        """
    )

    op.execute(
        """
        CREATE POLICY message_citations_select_own
        ON message_citations FOR SELECT TO authenticated
        USING (
            EXISTS (
                SELECT 1
                FROM chat_messages m
                JOIN chat_threads t ON t.id = m.thread_id
                WHERE m.id = message_citations.message_id
                  AND t.user_id = auth.uid()
            )
        )
        """
    )
    op.execute(
        """
        CREATE POLICY message_citations_insert_own
        ON message_citations FOR INSERT TO authenticated
        WITH CHECK (
            EXISTS (
                SELECT 1
                FROM chat_messages m
                JOIN chat_threads t ON t.id = m.thread_id
                WHERE m.id = message_citations.message_id
                  AND t.user_id = auth.uid()
            )
        )
        """
    )

    op.execute(
        """
        CREATE POLICY source_documents_select_authenticated
        ON source_documents FOR SELECT TO authenticated
        USING (true)
        """
    )
    op.execute(
        """
        CREATE POLICY document_chunks_select_authenticated
        ON document_chunks FOR SELECT TO authenticated
        USING (true)
        """
    )


def downgrade() -> None:
    for policy, table in (
        ("document_chunks_select_authenticated", "document_chunks"),
        ("source_documents_select_authenticated", "source_documents"),
        ("message_citations_insert_own", "message_citations"),
        ("message_citations_select_own", "message_citations"),
        ("chat_messages_delete_own", "chat_messages"),
        ("chat_messages_update_own", "chat_messages"),
        ("chat_messages_insert_own", "chat_messages"),
        ("chat_messages_select_own", "chat_messages"),
        ("chat_threads_delete_own", "chat_threads"),
        ("chat_threads_update_own", "chat_threads"),
        ("chat_threads_insert_own", "chat_threads"),
        ("chat_threads_select_own", "chat_threads"),
        ("profiles_insert_own", "profiles"),
        ("profiles_update_own", "profiles"),
        ("profiles_select_own", "profiles"),
    ):
        op.execute(f"DROP POLICY IF EXISTS {policy} ON {table}")

    op.drop_index("ix_message_citations_chunk_id", table_name="message_citations")
    op.drop_index("ix_message_citations_message_id", table_name="message_citations")
    op.drop_table("message_citations")

    op.drop_index("ix_chat_messages_thread_id", table_name="chat_messages")
    op.drop_table("chat_messages")

    op.execute("DROP INDEX IF EXISTS ix_document_chunks_embedding_hnsw")
    op.execute("DROP INDEX IF EXISTS ix_document_chunks_search_vector")
    op.drop_index("ix_document_chunks_metadata", table_name="document_chunks")
    op.drop_index("ix_document_chunks_document_id", table_name="document_chunks")
    op.drop_table("document_chunks")

    op.drop_index("ix_chat_threads_user_id", table_name="chat_threads")
    op.drop_table("chat_threads")

    op.drop_index("ix_source_documents_filing_year", table_name="source_documents")
    op.drop_index("ix_source_documents_ticker", table_name="source_documents")
    op.drop_table("source_documents")

    op.execute("ALTER TABLE profiles DROP CONSTRAINT IF EXISTS profiles_id_fkey")
    op.drop_table("profiles")

    op.execute("DROP EXTENSION IF EXISTS vector")
