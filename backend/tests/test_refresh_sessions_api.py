from uuid import uuid4

import httpx
import pytest

from app.main import app


@pytest.mark.asyncio
async def test_refresh_token_rotates_and_old_refresh_cannot_be_reused():
    email = f"refresh-{uuid4().hex}@example.com"
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
                "full_name": "Refresh Test",
            },
        )
        assert register.status_code == 202, register.text

        verify = await client.post(
            "/api/v1/auth/register/verify",
            json={"email": email, "code": "123456"},
        )
        assert verify.status_code == 200, verify.text
        body = verify.json()
        assert body["refresh_token"]
        first_refresh = body["refresh_token"]

        rotated = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": first_refresh},
        )
        assert rotated.status_code == 200, rotated.text
        second_refresh = rotated.json()["refresh_token"]
        assert second_refresh
        assert second_refresh != first_refresh

        reused = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": first_refresh},
        )
        assert reused.status_code == 401, reused.text

        current = await client.get(
            "/api/v1/auth/me",
            headers={
                "Authorization": "Bearer " + rotated.json()["access_token"]
            },
        )
        assert current.status_code == 200, current.text


@pytest.mark.asyncio
async def test_revoke_sessions_invalidates_old_refresh_and_returns_new_refresh():
    email = f"refresh-revoke-{uuid4().hex}@example.com"
    password = "StrongPass123!"

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(
        transport=transport,
        base_url="http://testserver",
    ) as client:
        await client.post(
            "/api/v1/auth/register",
            json={
                "email": email,
                "password": password,
                "full_name": "Refresh Revoke Test",
            },
        )
        verify = await client.post(
            "/api/v1/auth/register/verify",
            json={"email": email, "code": "123456"},
        )
        body = verify.json()
        old_refresh = body["refresh_token"]

        revoke = await client.post(
            "/api/v1/security/revoke-sessions",
            headers={
                "Authorization": "Bearer " + body["access_token"]
            },
        )
        assert revoke.status_code == 200, revoke.text
        replacement_refresh = revoke.json()["refresh_token"]
        assert replacement_refresh
        assert replacement_refresh != old_refresh

        old_result = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": old_refresh},
        )
        assert old_result.status_code == 401, old_result.text

        new_result = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": replacement_refresh},
        )
        assert new_result.status_code == 200, new_result.text


@pytest.mark.asyncio
async def test_password_reset_invalidates_refresh_session():
    email = f"refresh-reset-{uuid4().hex}@example.com"
    password = "StrongPass123!"
    new_password = "NewStrongPass456!"

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(
        transport=transport,
        base_url="http://testserver",
    ) as client:
        await client.post(
            "/api/v1/auth/register",
            json={
                "email": email,
                "password": password,
                "full_name": "Refresh Reset Test",
            },
        )
        verify = await client.post(
            "/api/v1/auth/register/verify",
            json={"email": email, "code": "123456"},
        )
        refresh = verify.json()["refresh_token"]

        forgot = await client.post(
            "/api/v1/auth/password/forgot",
            json={"email": email},
        )
        assert forgot.status_code == 200

        reset = await client.post(
            "/api/v1/auth/password/reset",
            json={
                "email": email,
                "code": "123456",
                "new_password": new_password,
            },
        )
        assert reset.status_code == 200, reset.text

        result = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": refresh},
        )
        assert result.status_code == 401, result.text


@pytest.mark.asyncio
async def test_login_is_temporarily_locked_after_repeated_wrong_passwords():
    email = f"login-lock-{uuid4().hex}@example.com"
    password = "StrongPass123!"

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(
        transport=transport,
        base_url="http://testserver",
    ) as client:
        await client.post(
            "/api/v1/auth/register",
            json={
                "email": email,
                "password": password,
                "full_name": "Login Lock Test",
            },
        )
        verify = await client.post(
            "/api/v1/auth/register/verify",
            json={"email": email, "code": "123456"},
        )
        assert verify.status_code == 200

        for _ in range(5):
            failed = await client.post(
                "/api/v1/auth/login",
                json={"email": email, "password": "WrongPassword999!"},
            )
            assert failed.status_code == 401, failed.text

        locked = await client.post(
            "/api/v1/auth/login",
            json={"email": email, "password": password},
        )
        assert locked.status_code == 429, locked.text
        assert int(locked.headers["retry-after"]) >= 1
