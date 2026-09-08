import base64
import json

from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.db.session import get_db
from app.dependencies.auth import get_current_user
from app.models.user import Entitlement, EntitlementStatus, PlanCode, User
from app.schemas.subscriptions import (
    GooglePlayVerifyRequest,
    GooglePlayVerifyResponse,
    SubscriptionStatusResponse,
)
from app.services.google_play import get_google_play_verifier
from app.services.subscriptions import apply_paid_entitlement, normalize_paid_entitlement
from app.services.trials import normalize_entitlement

router = APIRouter(prefix="/subscriptions", tags=["subscriptions"])
settings = get_settings()


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
        provider_product_id=payload.product_id,
        paid_until=result.expiry_time,
    )
    await db.commit()

    try:
        await verifier.acknowledge_subscription(
            product_id=payload.product_id,
            purchase_token=payload.purchase_token,
        )
    except Exception:
        pass

    return GooglePlayVerifyResponse(
        verified=True,
        plan_code=user.entitlement.plan_code.value,
        status=user.entitlement.status.value,
        paid_until=user.entitlement.paid_until,
    )


@router.post("/google-play/rtdn", status_code=status.HTTP_204_NO_CONTENT)
async def google_play_rtdn(
    payload: dict,
    authorization: str | None = Header(default=None),
    db: AsyncSession = Depends(get_db),
) -> None:
    expected = settings.google_play_rtdn_secret
    if expected:
        if authorization != "Bearer " + expected:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid RTDN secret")

    message = payload.get("message") or {}
    encoded = message.get("data")
    if not encoded:
        return None

    try:
        decoded = base64.b64decode(encoded).decode("utf-8")
        notification = json.loads(decoded)
    except Exception as exc:
        raise HTTPException(status_code=400, detail="Invalid RTDN payload") from exc

    if notification.get("packageName") != settings.google_play_package_name:
        raise HTTPException(status_code=400, detail="Unexpected package name")

    subscription_notification = notification.get("subscriptionNotification")
    if not subscription_notification:
        return None

    purchase_token = subscription_notification.get("purchaseToken")
    if not purchase_token:
        return None

    entitlement = await db.scalar(
        select(Entitlement).where(
            Entitlement.provider == "google_play",
            Entitlement.provider_subscription_id == purchase_token,
        )
    )
    if entitlement is None or not entitlement.provider_product_id:
        return None

    verifier = get_google_play_verifier()
    result = await verifier.verify_subscription(
        product_id=entitlement.provider_product_id,
        purchase_token=purchase_token,
    )

    if result.verified and result.expiry_time is not None:
        apply_paid_entitlement(
            entitlement,
            provider="google_play",
            provider_subscription_id=purchase_token,
            provider_product_id=entitlement.provider_product_id,
            paid_until=result.expiry_time,
        )
    else:
        entitlement.status = EntitlementStatus.EXPIRED
        entitlement.plan_code = PlanCode.FREE

    await db.commit()
