import pytest

from app.core.config import Settings
from app.core.production import ProductionConfigError, validate_production_settings


def test_development_does_not_require_production_secrets():
    settings = Settings(environment="development")
    validate_production_settings(settings)


def test_production_rejects_default_jwt_secret():
    settings = Settings(
        environment="production",
        database_url="postgresql+asyncpg://user:pass@db/finpilot",
        cors_origins="https://admin.example.com",
        jwt_secret="change-me-in-production",
    )

    with pytest.raises(ProductionConfigError):
        validate_production_settings(settings)


def test_production_rejects_log_only_email_delivery():
    settings = Settings(
        environment="production",
        database_url="postgresql+asyncpg://user:pass@db/finpilot",
        cors_origins="https://admin.example.com",
        jwt_secret="a-very-long-production-secret",
        email_delivery_mode="log",
    )

    with pytest.raises(ProductionConfigError):
        validate_production_settings(settings)


def test_production_accepts_resend_email_delivery():
    settings = Settings(
        environment="production",
        database_url="postgresql+asyncpg://user:pass@db/finpilot",
        cors_origins="https://admin.example.com",
        jwt_secret="a-very-long-production-secret",
        email_delivery_mode="resend",
        resend_api_key="re_test_key",
        resend_from_email="no-reply@example.com",
    )

    validate_production_settings(settings)
