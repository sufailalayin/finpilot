from uuid import uuid4

import httpx
import pytest
from sqlalchemy import select

from app.db.session import AsyncSessionLocal
from app.main import app
from app.models.user import User


async def _register_and_verify(client: httpx.AsyncClient, email: str, password: str) -> None:
    register = await client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": password,
            "full_name": "Login Surface Test",
        },
    )
    assert register.status_code == 202, register.text

    verify = await client.post(
        "/api/v1/auth/register/verify",
        json={"email": email, "code": "123456"},
    )
    assert verify.status_code == 200, verify.text


@pytest.mark.asyncio
async def test_customer_and_admin_login_surfaces_are_separated():
    password = "StrongPass123!"
    customer_email = f"customer-surface-{uuid4().hex}@example.com"
    admin_email = f"admin-surface-{uuid4().hex}@example.com"

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(
        transport=transport,
        base_url="http://testserver",
    ) as client:
        await _register_and_verify(client, customer_email, password)

        customer_admin_login = await client.post(
            "/api/v1/auth/admin/login",
            json={"email": customer_email, "password": password},
        )
        assert customer_admin_login.status_code == 403, customer_admin_login.text
        assert customer_admin_login.json()["detail"] == "Administrator access required"

        await _register_and_verify(client, admin_email, password)

        async with AsyncSessionLocal() as db:
            admin = await db.scalar(select(User).where(User.email == admin_email))
            assert admin is not None
            admin.is_admin = True
            await db.commit()

        admin_customer_login = await client.post(
            "/api/v1/auth/login",
            json={"email": admin_email, "password": password},
        )
        assert admin_customer_login.status_code == 403, admin_customer_login.text
        assert (
            admin_customer_login.json()["detail"]
            == "Administrator accounts must use the administrator portal"
        )

        admin_portal_login = await client.post(
            "/api/v1/auth/admin/login",
            json={"email": admin_email, "password": password},
        )
        assert admin_portal_login.status_code == 200, admin_portal_login.text
        assert admin_portal_login.json()["user"]["is_admin"] is True
