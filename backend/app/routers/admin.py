from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.dependencies.admin import get_current_admin
from app.models.ai import AIUsageEvent
from app.models.asset import Asset
from app.models.finance import FinanceAccount, Transaction
from app.models.liability import Liability
from app.models.user import (
    Entitlement,
    EntitlementStatus,
    PlanCode,
    SecurityAuditEvent,
    User,
)
from app.schemas.admin import (
    AdminAIUsageSummary,
    AdminOverview,
    AdminSecurityEventRow,
    AdminSubscriptionSummary,
    AdminUserRow,
)

router = APIRouter(prefix="/admin", tags=["admin"])


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


@router.get("/overview", response_model=AdminOverview)
async def overview(
    _: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> AdminOverview:
    now = _utcnow()
    seven_days_ago = now - timedelta(days=7)
    day_ago = now - timedelta(hours=24)

    total_users = await db.scalar(select(func.count(User.id))) or 0
    active_trials = await db.scalar(
        select(func.count(Entitlement.id)).where(Entitlement.status == EntitlementStatus.TRIAL)
    ) or 0
    paid_users = await db.scalar(
        select(func.count(Entitlement.id)).where(
            Entitlement.plan_code == PlanCode.PRO,
            Entitlement.status == EntitlementStatus.ACTIVE,
        )
    ) or 0
    expired_entitlements = await db.scalar(
        select(func.count(Entitlement.id)).where(Entitlement.status == EntitlementStatus.EXPIRED)
    ) or 0
    ai_requests = await db.scalar(select(func.count(AIUsageEvent.id))) or 0
    registrations_7d = await db.scalar(
        select(func.count(User.id)).where(User.created_at >= seven_days_ago)
    ) or 0
    finance_accounts = await db.scalar(select(func.count(FinanceAccount.id))) or 0
    transactions = await db.scalar(select(func.count(Transaction.id))) or 0
    assets = await db.scalar(select(func.count(Asset.id))) or 0
    liabilities = await db.scalar(select(func.count(Liability.id))) or 0
    security_events_24h = await db.scalar(
        select(func.count(SecurityAuditEvent.id)).where(SecurityAuditEvent.created_at >= day_ago)
    ) or 0

    return AdminOverview(
        total_users=total_users,
        active_trials=active_trials,
        paid_users=paid_users,
        expired_entitlements=expired_entitlements,
        ai_requests=ai_requests,
        registrations_7d=registrations_7d,
        finance_accounts=finance_accounts,
        transactions=transactions,
        assets=assets,
        liabilities=liabilities,
        security_events_24h=security_events_24h,
    )


@router.get("/users", response_model=list[AdminUserRow])
async def users(
    q: str | None = Query(default=None, max_length=120),
    limit: int = Query(default=200, ge=1, le=500),
    _: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> list[AdminUserRow]:
    statement = (
        select(User, Entitlement)
        .outerjoin(Entitlement, Entitlement.user_id == User.id)
        .order_by(User.created_at.desc())
        .limit(limit)
    )
    if q:
        term = f"%{q.strip()}%"
        statement = statement.where(
            or_(
                User.email.ilike(term),
                User.full_name.ilike(term),
            )
        )

    rows = await db.execute(statement)

    return [
        AdminUserRow(
            id=str(user.id),
            email=user.email,
            full_name=user.full_name,
            user_status=user.status.value,
            is_admin=user.is_admin,
            entitlement_status=entitlement.status.value if entitlement else None,
            plan_code=entitlement.plan_code.value if entitlement else None,
            trial_ends_at=entitlement.trial_ends_at if entitlement else None,
            paid_until=entitlement.paid_until if entitlement else None,
            created_at=user.created_at,
        )
        for user, entitlement in rows.all()
    ]


@router.get("/subscriptions", response_model=AdminSubscriptionSummary)
async def subscriptions(
    _: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> AdminSubscriptionSummary:
    free_users = await db.scalar(
        select(func.count(Entitlement.id)).where(Entitlement.plan_code == PlanCode.FREE)
    ) or 0
    trial_users = await db.scalar(
        select(func.count(Entitlement.id)).where(Entitlement.status == EntitlementStatus.TRIAL)
    ) or 0
    active_paid_users = await db.scalar(
        select(func.count(Entitlement.id)).where(
            Entitlement.plan_code == PlanCode.PRO,
            Entitlement.status == EntitlementStatus.ACTIVE,
        )
    ) or 0
    cancelled_users = await db.scalar(
        select(func.count(Entitlement.id)).where(Entitlement.status == EntitlementStatus.CANCELLED)
    ) or 0
    expired_users = await db.scalar(
        select(func.count(Entitlement.id)).where(Entitlement.status == EntitlementStatus.EXPIRED)
    ) or 0

    return AdminSubscriptionSummary(
        free_users=free_users,
        trial_users=trial_users,
        active_paid_users=active_paid_users,
        cancelled_users=cancelled_users,
        expired_users=expired_users,
    )


@router.get("/ai-usage", response_model=AdminAIUsageSummary)
async def ai_usage(
    _: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> AdminAIUsageSummary:
    now = _utcnow()
    day_ago = now - timedelta(hours=24)
    seven_days_ago = now - timedelta(days=7)

    total_requests = await db.scalar(select(func.count(AIUsageEvent.id))) or 0
    requests_24h = await db.scalar(
        select(func.count(AIUsageEvent.id)).where(AIUsageEvent.created_at >= day_ago)
    ) or 0
    requests_7d = await db.scalar(
        select(func.count(AIUsageEvent.id)).where(AIUsageEvent.created_at >= seven_days_ago)
    ) or 0
    unique_users_7d = await db.scalar(
        select(func.count(func.distinct(AIUsageEvent.user_id))).where(
            AIUsageEvent.created_at >= seven_days_ago
        )
    ) or 0
    prompt_chars_7d = await db.scalar(
        select(func.coalesce(func.sum(AIUsageEvent.prompt_chars), 0)).where(
            AIUsageEvent.created_at >= seven_days_ago
        )
    ) or 0
    response_chars_7d = await db.scalar(
        select(func.coalesce(func.sum(AIUsageEvent.response_chars), 0)).where(
            AIUsageEvent.created_at >= seven_days_ago
        )
    ) or 0

    return AdminAIUsageSummary(
        total_requests=int(total_requests),
        requests_24h=int(requests_24h),
        requests_7d=int(requests_7d),
        unique_users_7d=int(unique_users_7d),
        prompt_chars_7d=int(prompt_chars_7d),
        response_chars_7d=int(response_chars_7d),
    )


@router.get("/security-events", response_model=list[AdminSecurityEventRow])
async def security_events(
    limit: int = Query(default=100, ge=1, le=500),
    _: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> list[AdminSecurityEventRow]:
    rows = await db.execute(
        select(SecurityAuditEvent, User.email)
        .outerjoin(User, User.id == SecurityAuditEvent.user_id)
        .order_by(SecurityAuditEvent.created_at.desc())
        .limit(limit)
    )
    return [
        AdminSecurityEventRow(
            id=str(event.id),
            user_id=str(event.user_id) if event.user_id else None,
            user_email=email,
            event_type=event.event_type,
            description=event.description,
            ip_address=event.ip_address,
            user_agent=event.user_agent,
            created_at=event.created_at,
        )
        for event, email in rows.all()
    ]
