from app.core.config import Settings


class ProductionConfigError(RuntimeError):
    pass


def validate_production_settings(settings: Settings) -> None:
    if settings.environment != "production":
        return

    missing: list[str] = []

    if not settings.database_url:
        missing.append("FINPILOT_DATABASE_URL")
    if (
        not settings.jwt_secret
        or settings.jwt_secret == "change-me-in-production"
        or len(settings.jwt_secret) < 32
    ):
        missing.append("FINPILOT_JWT_SECRET (minimum 32 characters)")
    if not settings.cors_origins:
        missing.append("FINPILOT_CORS_ORIGINS")
    else:
        origins = [
            origin.strip()
            for origin in settings.cors_origins.split(",")
            if origin.strip()
        ]
        if "*" in origins:
            missing.append("FINPILOT_CORS_ORIGINS (wildcard is not allowed)")
        if any(
            origin.startswith("http://")
            and "localhost" not in origin
            and "127.0.0.1" not in origin
            for origin in origins
        ):
            missing.append("FINPILOT_CORS_ORIGINS (HTTPS required in production)")

    if settings.otp_test_code:
        missing.append("FINPILOT_OTP_TEST_CODE must be empty in production")

    if settings.jwt_algorithm != "HS256":
        missing.append("FINPILOT_JWT_ALGORITHM must be HS256")

    if (
        settings.google_play_package_name
        or settings.google_play_service_account_json
    ) and not settings.google_play_rtdn_secret:
        missing.append("FINPILOT_GOOGLE_PLAY_RTDN_SECRET")

    email_mode = settings.email_delivery_mode.lower()
    if email_mode == "resend":
        if not settings.resend_api_key or not settings.resend_from_email:
            missing.append("Resend OTP email configuration")
    elif email_mode == "smtp":
        if not settings.smtp_host or not settings.smtp_from_email:
            missing.append("SMTP OTP email configuration")
    else:
        missing.append(
            "FINPILOT_EMAIL_DELIVERY_MODE must be resend or smtp in production"
        )

    if missing:
        raise ProductionConfigError(
            "Missing or unsafe production configuration: " + ", ".join(missing)
        )
