from uuid import uuid4

import httpx
import pytest

from app.main import app


@pytest.mark.asyncio
async def test_signup_requires_email_verification_and_password_reset_revokes_session():
    email = f"auth-{uuid4().hex}@example.com"
    password = "StrongPass123!"
    new_password = "NewStrongPass456!"

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
                "full_name": "OTP Test",
            },
        )
        assert register.status_code == 202, register.text
        assert register.json()["verification_required"] is True

        unverified_login = await client.post(
            "/api/v1/auth/login",
            json={"email": email, "password": password},
        )
        assert unverified_login.status_code == 403, unverified_login.text

        verify = await client.post(
            "/api/v1/auth/register/verify",
            json={"email": email, "code": "123456"},
        )
        assert verify.status_code == 200, verify.text
        old_token = verify.json()["access_token"]
        headers = {"Authorization": f"Bearer {old_token}"}

        me = await client.get("/api/v1/auth/me", headers=headers)
        assert me.status_code == 200, me.text
        assert me.json()["email_verified"] is True

        forgot = await client.post(
            "/api/v1/auth/password/forgot",
            json={"email": email},
        )
        assert forgot.status_code == 200, forgot.text

        reset = await client.post(
            "/api/v1/auth/password/reset",
            json={
                "email": email,
                "code": "123456",
                "new_password": new_password,
            },
        )
        assert reset.status_code == 200, reset.text

        old_session = await client.get("/api/v1/auth/me", headers=headers)
        assert old_session.status_code == 401, old_session.text

        old_password_login = await client.post(
            "/api/v1/auth/login",
            json={"email": email, "password": password},
        )
        assert old_password_login.status_code == 401, old_password_login.text

        new_password_login = await client.post(
            "/api/v1/auth/login",
            json={"email": email, "password": new_password},
        )
        assert new_password_login.status_code == 200, new_password_login.text


@pytest.mark.asyncio
async def test_forgot_password_response_does_not_reveal_unknown_email():
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(
        transport=transport,
        base_url="http://testserver",
    ) as client:
        response = await client.post(
            "/api/v1/auth/password/forgot",
            json={"email": f"unknown-{uuid4().hex}@example.com"},
        )
        assert response.status_code == 200, response.text
        assert "If an account exists" in response.json()["message"]



@pytest.mark.asyncio
async def test_signup_otp_resend_is_rate_limited_and_wrong_code_is_rejected():
    email = f"otp-rate-{uuid4().hex}@example.com"
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
                "full_name": "OTP Rate Test",
            },
        )
        assert register.status_code == 202, register.text

        resend = await client.post(
            "/api/v1/auth/register/resend",
            json={"email": email},
        )
        assert resend.status_code == 429, resend.text
        assert int(resend.headers["retry-after"]) >= 1

        wrong = await client.post(
            "/api/v1/auth/register/verify",
            json={"email": email, "code": "000000"},
        )
        assert wrong.status_code == 400, wrong.text

        correct = await client.post(
            "/api/v1/auth/register/verify",
            json={"email": email, "code": "123456"},
        )
        assert correct.status_code == 200, correct.text
        assert correct.json()["user"]["email_verified"] is True
