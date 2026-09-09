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


    if missing:
        raise ProductionConfigError(
            "Missing or unsafe production configuration: " + ", ".join(missing)
        )
