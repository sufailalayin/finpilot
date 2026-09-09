import base64
import hashlib
import json
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.db.session import get_db
from app.dependencies.auth import get_current_user
from app.dependencies.entitlements import require_pro_user
from app.models.user import BillingPlan, Entitlement, EntitlementStatus, PaymentRecord, PlanCode, User
from app.schemas.subscriptions import (
    GooglePlayVerifyRequest,
    GooglePlayVerifyResponse,
    SubscriptionFeaturesResponse,
    FeatureAccess,
    SubscriptionStatusResponse,
    PublicBillingPlan,
    PublicBillingPlansResponse,
)
from app.services.entitlements import has_pro_access
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

    billing_plan = None
    if entitlement.billing_plan_id is not None:
        billing_plan = await db.scalar(
            select(BillingPlan).where(BillingPlan.id == entitlement.billing_plan_id)
        )

    return SubscriptionStatusResponse(
        plan_code=entitlement.plan_code.value,
        status=entitlement.status.value,
        trial_ends_at=entitlement.trial_ends_at,
        paid_until=entitlement.paid_until,
        provider=entitlement.provider,
        billing_plan_id=str(entitlement.billing_plan_id) if entitlement.billing_plan_id else None,
        billing_plan_name=billing_plan.name if billing_plan else None,
    )


@router.get("/plans", response_model=PublicBillingPlansResponse)
async def public_billing_plans(
    _: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> PublicBillingPlansResponse:
    rows = list(
        (
            await db.execute(
                select(BillingPlan)
                .where(
                    BillingPlan.is_active.is_(True),
                    BillingPlan.access_level == "pro",
                )
                .order_by(BillingPlan.price.asc(), BillingPlan.created_at.asc())
            )
        ).scalars().all()
    )
    return PublicBillingPlansResponse(
        plans=[
            PublicBillingPlan(
                id=str(plan.id),
                code=plan.code,
                name=plan.name,
                access_level=plan.access_level,
                billing_period=plan.billing_period,
                price=float(plan.price),
                currency=plan.currency,
                description=plan.description,
                features=plan.features,
                google_play_product_id=plan.google_play_product_id,
            )
            for plan in rows
        ]
    )


@router.post("/google-play/verify", response_model=GooglePlayVerifyResponse)
async def verify_google_play(
    payload: GooglePlayVerifyRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> GooglePlayVerifyResponse:
    try:
        import uuid
        billing_plan_id = uuid.UUID(payload.billing_plan_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid billing plan id") from exc

    plan = await db.scalar(
        select(BillingPlan).where(
            BillingPlan.id == billing_plan_id,
            BillingPlan.is_active.is_(True),
            BillingPlan.access_level == "pro",
        )
    )
    if plan is None:
        raise HTTPException(status_code=404, detail="Billing plan not found")
    if not plan.google_play_product_id:
        raise HTTPException(
            status_code=400,
            detail="This plan is not configured for Google Play payment",
        )
    if payload.product_id != plan.google_play_product_id:
        raise HTTPException(status_code=400, detail="Selected plan does not match product")

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

    entitlement = user.entitlement
    apply_paid_entitlement(
        entitlement,
        provider="google_play",
        provider_subscription_id=payload.purchase_token,
        provider_product_id=payload.product_id,
        paid_until=result.expiry_time,
    )
    entitlement.billing_plan_id = plan.id

    payment_reference = hashlib.sha256(payload.purchase_token.encode("utf-8")).hexdigest()
    existing_payment = await db.scalar(
        select(PaymentRecord).where(
            PaymentRecord.user_id == user.id,
            PaymentRecord.provider == "google_play",
            PaymentRecord.reference == payment_reference,
        )
    )
    if existing_payment is None:
        db.add(
            PaymentRecord(
                user_id=user.id,
                billing_plan_id=plan.id,
                amount=plan.price,
                currency=plan.currency,
                payment_method="google_play",
                provider="google_play",
                reference=payment_reference,
                status="received",
                notes="Verified Google Play subscription purchase",
                received_at=datetime.now(timezone.utc),
                recorded_by_admin_id=None,
            )
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
        plan_code=entitlement.plan_code.value,
        status=entitlement.status.value,
        paid_until=entitlement.paid_until,
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



@router.get("/features", response_model=SubscriptionFeaturesResponse)
async def subscription_features(
    user: User = Depends(get_current_user),
) -> SubscriptionFeaturesResponse:
    entitlement = user.entitlement
    pro = has_pro_access(entitlement)
    plan_code = entitlement.plan_code.value if entitlement is not None else "free"
    status_value = entitlement.status.value if entitlement is not None else "expired"

    definitions = [
        ("core_accounts", "Accounts & transactions", False),
        ("basic_dashboard", "Core dashboard", False),
        ("basic_budgets", "Basic budgets & goals", False),
        ("ai_copilot", "AI Financial Copilot", True),
        ("advanced_reports", "Advanced reports & exports", True),
        ("smart_budgeting", "Forecast budgets & goal planner", True),
        ("smart_alerts", "Smart financial alerts", True),
        ("assets_liabilities", "Assets, investments, loans & EMI analytics", True),
        ("health_score", "Financial Health Score 2.0", True),
        ("security_privacy", "Security & privacy controls", False),
    ]

    return SubscriptionFeaturesResponse(
        plan_code=plan_code,
        status=status_value,
        has_pro_access=pro,
        features=[
            FeatureAccess(
                code=code,
                name=name,
                premium=premium,
                included=(pro or not premium),
            )
            for code, name, premium in definitions
        ],
    )
