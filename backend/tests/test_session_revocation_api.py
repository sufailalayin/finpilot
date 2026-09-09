from uuid import uuid4

import httpx
import pytest

from app.main import app


@pytest.mark.asyncio
async def test_revoke_sessions_invalidates_old_token_and_returns_working_replacement():
    email = f"session-{uuid4().hex}@example.com"
    password = "StrongPass123!"

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(
        transport=transport,
        base_url="http://testserver",
    ) as client:
        register = await client.post(
            "/api/v1/auth/register",
            json={
                "email": email,
                "password": password,
                "full_name": "Session Test",
            },
        )
        assert register.status_code == 201, register.text

        old_token = register.json()["access_token"]
        old_headers = {"Authorization": f"Bearer {old_token}"}

        before = await client.get("/api/v1/auth/me", headers=old_headers)
        assert before.status_code == 200, before.text

        revoke = await client.post(
            "/api/v1/security/revoke-sessions",
            headers=old_headers,
        )
        assert revoke.status_code == 200, revoke.text
        new_token = revoke.json()["access_token"]
        assert new_token != old_token

        old_after = await client.get(
            "/api/v1/auth/me",
            headers=old_headers,
        )
        assert old_after.status_code == 401, old_after.text

        new_after = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {new_token}"},
        )
        assert new_after.status_code == 200, new_after.text
        assert new_after.json()["email"] == email
