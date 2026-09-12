import asyncio
from types import SimpleNamespace

import app.database.supabase as supabase_module
from app.config import settings


def test_service_role_client_uses_opaque_secret_only_as_api_key(monkeypatch) -> None:
    fake_client = SimpleNamespace(
        options=SimpleNamespace(headers={"Authorization": "Bearer sb_secret_test"})
    )

    async def fake_create_client(*args, **kwargs):
        return fake_client

    monkeypatch.setattr(supabase_module, "create_async_client", fake_create_client)
    monkeypatch.setattr(settings, "SUPABASE_SERVICE_ROLE_KEY", "sb_secret_test")

    client = asyncio.run(supabase_module.create_service_role_client())

    assert client is fake_client
    assert "Authorization" not in client.options.headers
