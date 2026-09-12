"""Add secured pgvector and full-text retrieval RPCs.

Revision ID: c4f92e7a1b6d
Revises: a8f3c1d20e4b
Create Date: 2026-09-12 22:40:00.000000

"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "c4f92e7a1b6d"
down_revision: str | Sequence[str] | None = "a8f3c1d20e4b"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        """
        CREATE FUNCTION public.match_document_chunks(
            query_embedding vector(1536),
            match_count integer DEFAULT 50,
            filter_tickers text[] DEFAULT NULL,
            filter_filing_types text[] DEFAULT NULL,
            filter_start_year integer DEFAULT NULL,
            filter_end_year integer DEFAULT NULL
        )
        RETURNS TABLE (chunk_id uuid, score double precision)
        LANGUAGE sql
        STABLE
        SECURITY INVOKER
        SET search_path = public, pg_catalog
        AS $$
            SELECT
                dc.id AS chunk_id,
                1 - (dc.embedding <=> query_embedding) AS score
            FROM public.document_chunks AS dc
            JOIN public.source_documents AS sd ON sd.id = dc.document_id
            WHERE dc.embedding IS NOT NULL
              AND (
                  filter_tickers IS NULL
                  OR sd.ticker::text = ANY(filter_tickers)
              )
              AND (
                  filter_filing_types IS NULL
                  OR sd.filing_type::text = ANY(filter_filing_types)
              )
              AND (
                  filter_start_year IS NULL
                  OR sd.filing_year >= filter_start_year
              )
              AND (
                  filter_end_year IS NULL
                  OR sd.filing_year <= filter_end_year
              )
            ORDER BY dc.embedding <=> query_embedding, dc.id
            LIMIT LEAST(GREATEST(COALESCE(match_count, 50), 1), 100)
        $$;
        """
    )
    op.execute(
        """
        CREATE FUNCTION public.search_document_chunks(
            search_query text,
            match_count integer DEFAULT 50,
            filter_tickers text[] DEFAULT NULL,
            filter_filing_types text[] DEFAULT NULL,
            filter_start_year integer DEFAULT NULL,
            filter_end_year integer DEFAULT NULL
        )
        RETURNS TABLE (chunk_id uuid, score double precision)
        LANGUAGE sql
        STABLE
        SECURITY INVOKER
        SET search_path = public, pg_catalog
        AS $$
            WITH parsed_query AS (
                SELECT websearch_to_tsquery('english', search_query) AS value
            )
            SELECT
                dc.id AS chunk_id,
                ts_rank_cd(dc.search_vector, parsed_query.value)::double precision AS score
            FROM public.document_chunks AS dc
            JOIN public.source_documents AS sd ON sd.id = dc.document_id
            CROSS JOIN parsed_query
            WHERE parsed_query.value <> ''::tsquery
              AND dc.search_vector @@ parsed_query.value
              AND (
                  filter_tickers IS NULL
                  OR sd.ticker::text = ANY(filter_tickers)
              )
              AND (
                  filter_filing_types IS NULL
                  OR sd.filing_type::text = ANY(filter_filing_types)
              )
              AND (
                  filter_start_year IS NULL
                  OR sd.filing_year >= filter_start_year
              )
              AND (
                  filter_end_year IS NULL
                  OR sd.filing_year <= filter_end_year
              )
            ORDER BY score DESC, dc.id
            LIMIT LEAST(GREATEST(COALESCE(match_count, 50), 1), 100)
        $$;
        """
    )

    op.execute(
        """
        REVOKE ALL ON FUNCTION public.match_document_chunks(
            vector, integer, text[], text[], integer, integer
        ) FROM PUBLIC
        """
    )
    op.execute(
        """
        REVOKE ALL ON FUNCTION public.search_document_chunks(
            text, integer, text[], text[], integer, integer
        ) FROM PUBLIC
        """
    )
    op.execute(
        """
        GRANT EXECUTE ON FUNCTION public.match_document_chunks(
            vector, integer, text[], text[], integer, integer
        ) TO authenticated, service_role
        """
    )
    op.execute(
        """
        GRANT EXECUTE ON FUNCTION public.search_document_chunks(
            text, integer, text[], text[], integer, integer
        ) TO authenticated, service_role
        """
    )


def downgrade() -> None:
    op.execute(
        """
        DROP FUNCTION IF EXISTS public.search_document_chunks(
            text, integer, text[], text[], integer, integer
        )
        """
    )
    op.execute(
        """
        DROP FUNCTION IF EXISTS public.match_document_chunks(
            vector, integer, text[], text[], integer, integer
        )
        """
    )
