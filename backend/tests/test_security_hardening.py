from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest

from app.core.config import Settings
from app.core.production import ProductionConfigError, validate_production_settings
from app.core.security import create_access_token, decode_access_token_claims
from app.models.user import User, UserStatus
from app.routers.security_privacy import _export_profile
from app.services.login_security import (
    clear_login_failures,
    lock_seconds_remaining,
    record_login_failure,
)


def _production_settings(**overrides):
    values = {
        "environment": "production",
        "database_url": "postgresql+asyncpg://user:password@db:5432/finpilot",
        "jwt_secret": "x" * 48,
        "cors_origins": "https://admin.example.com",
        "otp_test_code": "",
        "jwt_algorithm": "HS256",
    }
    values.update(overrides)
    return Settings(**values)


def test_production_rejects_short_jwt_secret():
    with pytest.raises(ProductionConfigError):
        validate_production_settings(
            _production_settings(jwt_secret="too-short")
        )


def test_production_rejects_wildcard_cors():
    with pytest.raises(ProductionConfigError):
        validate_production_settings(
            _production_settings(cors_origins="*")
        )


def test_production_rejects_plain_http_cors():
    with pytest.raises(ProductionConfigError):
        validate_production_settings(
            _production_settings(cors_origins="http://example.com")
        )


def test_production_rejects_test_otp():
    with pytest.raises(ProductionConfigError):
        validate_production_settings(
            _production_settings(otp_test_code="123456")
        )


def test_export_profile_never_contains_auth_secrets():
    now = datetime.now(timezone.utc)
    user = User(
        id=uuid4(),
        email="user@example.com",
        password_hash="$2b$12$secret-hash",
        full_name="Test User",
        status=UserStatus.ACTIVE,
        is_admin=False,
        email_verified=True,
        token_version=7,
        failed_login_attempts=3,
        created_at=now,
        updated_at=now,
    )
    exported = _export_profile(user)
    assert "password_hash" not in exported
    assert "token_version" not in exported
    assert "failed_login_attempts" not in exported
    assert "login_locked_until" not in exported


def test_login_throttle_locks_and_resets():
    now = datetime.now(timezone.utc)
    user = User(
        email="user@example.com",
        password_hash="hash",
        failed_login_attempts=0,
        login_locked_until=None,
    )

    for _ in range(5):
        record_login_failure(user, now=now)

    assert lock_seconds_remaining(user, now=now) > 0

    clear_login_failures(user)
    assert user.failed_login_attempts == 0
    assert user.login_locked_until is None


def test_expired_login_lock_is_not_active():
    now = datetime.now(timezone.utc)
    user = User(
        email="user@example.com",
        password_hash="hash",
        failed_login_attempts=0,
        login_locked_until=now - timedelta(seconds=1),
    )
    assert lock_seconds_remaining(user, now=now) == 0



def test_admin_mfa_claim_is_cryptographically_bound_to_token():
    token = create_access_token(
        str(uuid4()),
        token_version=4,
        admin_mfa=True,
    )
    claims = decode_access_token_claims(token)
    assert claims is not None
    assert claims["ver"] == 4
    assert claims["admin_mfa"] is True


def test_normal_access_token_does_not_gain_admin_mfa():
    token = create_access_token(str(uuid4()), token_version=1)
    claims = decode_access_token_claims(token)
    assert claims is not None
    assert claims["admin_mfa"] is False
