"""Supabase client factories.

User-scoped clients send the caller's JWT so Postgres RLS (`auth.uid()`) applies.
The service-role client bypasses RLS and must stay on the backend.
"""

from supabase import AsyncClient, AsyncClientOptions, create_async_client
from supabase.lib.client_options import DEFAULT_HEADERS

from app.config import settings


def _options(*, access_token: str | None = None) -> AsyncClientOptions:
    headers = dict(DEFAULT_HEADERS)
    if access_token is not None:
        headers["Authorization"] = f"Bearer {access_token}"
    return AsyncClientOptions(
        headers=headers,
        auto_refresh_token=False,
        persist_session=False,
    )


async def create_user_client(access_token: str) -> AsyncClient:
    """Anon-key client authenticated as the requesting user."""
    return await create_async_client(
        settings.SUPABASE_URL,
        settings.SUPABASE_ANON_KEY,
        options=_options(access_token=access_token),
    )


async def create_service_role_client() -> AsyncClient:
    """Privileged client for writes that cannot use the user JWT."""
    return await create_async_client(
        settings.SUPABASE_URL,
        settings.SUPABASE_SERVICE_ROLE_KEY,
        options=_options(access_token=settings.SUPABASE_SERVICE_ROLE_KEY),
    )
