from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.schemas.subscriptions import (
    GooglePlayVerifyRequest,
    GooglePlayVerifyResponse,
    SubscriptionStatusResponse,
)
from app.services.google_play import get_google_play_verifier
from app.services.subscriptions import apply_paid_entitlement, normalize_paid_entitlement
from app.services.trials import normalize_entitlement

router = APIRouter(prefix="/subscriptions", tags=["subscriptions"])


@router.get("/status", response_model=SubscriptionStatusResponse)
async def subscription_status(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> SubscriptionStatusResponse:
    entitlement = user.entitlement

    if entitlement is None:
        raise HTTPException(status_code=404, detail="Entitlement not found")

    previous_status = entitlement.status
    normalize_entitlement(entitlement)
    normalize_paid_entitlement(entitlement)

    if entitlement.status != previous_status:
        await db.commit()

    return SubscriptionStatusResponse(
        plan_code=entitlement.plan_code.value,
        status=entitlement.status.value,
        trial_ends_at=entitlement.trial_ends_at,
        paid_until=entitlement.paid_until,
        provider=entitlement.provider,
    )


@router.post("/google-play/verify", response_model=GooglePlayVerifyResponse)
async def verify_google_play(
    payload: GooglePlayVerifyRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> GooglePlayVerifyResponse:
    verifier = get_google_play_verifier()

    try:
        result = await verifier.verify_subscription(
            product_id=payload.product_id,
            purchase_token=payload.purchase_token,
        )
    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc

    if not result.verified or result.expiry_time is None:
        return GooglePlayVerifyResponse(
            verified=False,
            plan_code=user.entitlement.plan_code.value,
            status=user.entitlement.status.value,
            paid_until=user.entitlement.paid_until,
        )

    apply_paid_entitlement(
        user.entitlement,
        provider="google_play",
        provider_subscription_id=payload.purchase_token,
        paid_until=result.expiry_time,
    )
    await db.commit()

    return GooglePlayVerifyResponse(
        verified=True,
        plan_code=user.entitlement.plan_code.value,
        status=user.entitlement.status.value,
        paid_until=user.entitlement.paid_until,
    )
