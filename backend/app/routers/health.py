from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.core.config import get_settings

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
            detail="database unavailable",
        ) from exc

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

    return {
        "status": "ready",
        "email_delivery": "ready" if email_ready else "not_configured",
        "email_mode": email_mode,
    }
