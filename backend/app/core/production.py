from app.core.config import Settings


class ProductionConfigError(RuntimeError):
    pass


def validate_production_settings(settings: Settings) -> None:
    if settings.environment != "production":
        return

    missing: list[str] = []

    if not settings.database_url:
        missing.append("FINPILOT_DATABASE_URL")
    if not settings.jwt_secret or settings.jwt_secret == "change-me-in-production":
        missing.append("FINPILOT_JWT_SECRET")
    if not settings.cors_origins:
        missing.append("FINPILOT_CORS_ORIGINS")

    email_mode = settings.email_delivery_mode.lower().strip()
    if email_mode == "log":
        missing.append("FINPILOT_EMAIL_DELIVERY_MODE")

    if email_mode == "resend":
        if not settings.resend_api_key:
            missing.append("FINPILOT_RESEND_API_KEY")
        if not settings.resend_from_email:
            missing.append("FINPILOT_RESEND_FROM_EMAIL")
    elif email_mode == "smtp":
        if not settings.smtp_host:
            missing.append("FINPILOT_SMTP_HOST")
        if not settings.smtp_from_email:
            missing.append("FINPILOT_SMTP_FROM_EMAIL")
    elif email_mode not in {"resend", "smtp"}:
        missing.append("FINPILOT_EMAIL_DELIVERY_MODE")

    if missing:
        raise ProductionConfigError(
            "Missing or unsafe production configuration: " + ", ".join(missing)
        )
