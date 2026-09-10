from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.core.config import get_settings
from app.dependencies.admin import get_current_admin
from app.models.user import User

router = APIRouter(tags=["health"])
settings = get_settings()


@router.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/ready")
async def ready(db: AsyncSession = Depends(get_db)) -> dict[str, str]:
    try:
        await db.execute(text("SELECT 1"))
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="unavailable",
        ) from exc
    return {"status": "ready"}


@router.get("/admin/readiness")
async def admin_readiness(
    _: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    await db.execute(text("SELECT 1"))

    email_mode = settings.email_delivery_mode.lower()
    email_ready = (
        (
            email_mode == "smtp"
            and bool(settings.smtp_host)
            and bool(settings.smtp_from_email)
        )
        or (
            email_mode == "resend"
            and bool(settings.resend_api_key)
            and bool(settings.resend_from_email)
        )
    )
    google_play_ready = all(
        (
            settings.google_play_package_name,
            settings.google_play_service_account_json,
            settings.google_play_rtdn_secret,
        )
    )
    ai_ready = bool(settings.openai_api_key)
    cors_ready = bool(
        settings.cors_origins
        and "*" not in settings.cors_origins
        and "localhost" not in settings.cors_origins.lower()
    )
    production_ready = all(
        (
            email_ready,
            google_play_ready,
            ai_ready,
            cors_ready,
            settings.environment == "production",
        )
    )

    return {
        "status": "ready",
        "database": "ready",
        "environment": settings.environment,
        "email_delivery": "ready" if email_ready else "not_configured",
        "email_mode": email_mode,
        "google_play": "ready" if google_play_ready else "not_configured",
        "ai": "ready" if ai_ready else "not_configured",
        "cors": "ready" if cors_ready else "review_required",
        "production_release": "ready" if production_ready else "blocked",
    }
