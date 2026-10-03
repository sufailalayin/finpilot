from uuid import uuid4

import httpx
import pytest
from sqlalchemy import select

from app.db.session import AsyncSessionLocal
from app.main import app
from app.models.user import User


async def _register_and_promote_admin(
    client: httpx.AsyncClient,
    *,
    email: str,
    password: str,
) -> None:
    register = await client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": password,
            "full_name": "Admin Logout Test",
        },
    )
    assert register.status_code == 202, register.text

    verify = await client.post(
        "/api/v1/auth/register/verify",
        json={"email": email, "code": "123456"},
    )
    assert verify.status_code == 200, verify.text

    async with AsyncSessionLocal() as db:
        admin = await db.scalar(select(User).where(User.email == email))
        assert admin is not None
        admin.is_admin = True
        await db.commit()


@pytest.mark.asyncio
async def test_admin_logout_invalidates_mfa_access_token_server_side():
    password = "StrongPass123!"
    email = f"admin-logout-{uuid4().hex}@example.com"

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(
        transport=transport,
        base_url="http://testserver",
    ) as client:
        await _register_and_promote_admin(
            client,
            email=email,
            password=password,
        )

        login = await client.post(
            "/api/v1/auth/admin/login",
            json={"email": email, "password": password},
        )
        assert login.status_code == 200, login.text
        password_stage_token = login.json()["access_token"]

        mfa_request = await client.post(
            "/api/v1/auth/admin/mfa/request",
            headers={"Authorization": f"Bearer {password_stage_token}"},
        )
        assert mfa_request.status_code == 200, mfa_request.text

        mfa_verify = await client.post(
            "/api/v1/auth/admin/mfa/verify",
            json={"code": "123456"},
            headers={"Authorization": f"Bearer {password_stage_token}"},
        )
        assert mfa_verify.status_code == 200, mfa_verify.text
        admin_token = mfa_verify.json()["access_token"]
        admin_headers = {"Authorization": f"Bearer {admin_token}"}

        before_logout = await client.get(
            "/api/v1/admin/overview",
            headers=admin_headers,
        )
        assert before_logout.status_code == 200, before_logout.text

        logout = await client.post(
            "/api/v1/auth/admin/logout",
            headers=admin_headers,
        )
        assert logout.status_code == 200, logout.text

        after_logout = await client.get(
            "/api/v1/admin/overview",
            headers=admin_headers,
        )
        assert after_logout.status_code == 401, after_logout.text
        assert after_logout.json()["detail"] == "Session revoked"


@pytest.mark.asyncio
async def test_admin_logout_requires_mfa_bound_token():
    password = "StrongPass123!"
    email = f"admin-logout-mfa-{uuid4().hex}@example.com"

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(
        transport=transport,
        base_url="http://testserver",
    ) as client:
        await _register_and_promote_admin(
            client,
            email=email,
            password=password,
        )

        login = await client.post(
            "/api/v1/auth/admin/login",
            json={"email": email, "password": password},
        )
        assert login.status_code == 200, login.text

        logout = await client.post(
            "/api/v1/auth/admin/logout",
            headers={
                "Authorization": f"Bearer {login.json()['access_token']}"
            },
        )
        assert logout.status_code == 403, logout.text
        assert logout.json()["detail"] == "Administrator MFA verification required"
