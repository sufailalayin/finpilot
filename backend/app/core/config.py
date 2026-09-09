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

    otp_expiry_minutes: int = 10
    otp_resend_seconds: int = 60
    otp_max_attempts: int = 5
    otp_test_code: str = ""

    email_delivery_mode: str = "log"

    resend_api_key: str = ""
    resend_from_email: str = ""
    resend_from_name: str = "FinPilot"

    smtp_host: str = ""
    smtp_port: int = 587
    smtp_username: str = ""
    smtp_password: str = ""
    smtp_from_email: str = "no-reply@finpilot.app"
    smtp_from_name: str = "FinPilot"
    smtp_use_tls: bool = True

    google_play_package_name: str = ""
    google_play_monthly_product_id: str = "finpilot_pro_monthly"
    google_play_yearly_product_id: str = "finpilot_pro_yearly"
    google_play_service_account_json: str = ""
    google_play_rtdn_secret: str = ""

    openai_api_key: str = ""
    openai_model: str = "gpt-5.6-luna"

    cors_origins: str = "http://localhost:3000"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="FINPILOT_",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
