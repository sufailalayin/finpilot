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


def test_production_accepts_required_values():
    settings = Settings(
        environment="production",
        database_url="postgresql+asyncpg://user:pass@db/finpilot",
        cors_origins="https://admin.example.com",
        jwt_secret="a-very-long-production-secret",
    )

    validate_production_settings(settings)
