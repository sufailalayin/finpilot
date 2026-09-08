from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "FinPilot"
    environment: str = "development"
    database_url: str = "postgresql+asyncpg://finpilot:finpilot_dev@localhost:5432/finpilot"
    redis_url: str = "redis://localhost:6379/0"
    jwt_secret: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    access_token_minutes: int = 30
    trial_days: int = 7

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="FINPILOT_",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
