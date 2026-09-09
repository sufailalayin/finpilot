from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.dependencies.admin import get_current_admin
from app.models.ai import AIUsageEvent
from app.models.asset import Asset
from app.models.finance import FinanceAccount, Transaction
from app.models.liability import Liability
from app.models.user import (
    AdminActionLog,
    Entitlement,
    EntitlementStatus,
    PlanCode,
    SecurityAuditEvent,
    User,
    UserStatus,
)
from app.schemas.admin import (
    AdminActionLogRow,
    AdminAIUsageSummary,
    AdminOverview,
    AdminSecurityEventRow,
    AdminSubscriptionSummary,
    AdminUserRow,
    AdminUserUpdate,
)

router = APIRouter(prefix="/admin", tags=["admin"])


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _request_ip(request: Request) -> str | None:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()[:64]
    if request.client:
        return request.client.host[:64]
    return None


def _user_agent(request: Request) -> str | None:
    value = request.headers.get("user-agent")
    return value[:500] if value else None


def _state(user: User, entitlement: Entitlement | None) -> dict:
    return {
        "user_status": user.status.value,
        "plan_code": entitlement.plan_code.value if entitlement else None,
        "entitlement_status": entitlement.status.value if entitlement else None,
        "trial_ends_at": entitlement.trial_ends_at.isoformat() if entitlement and entitlement.trial_ends_at else None,
        "paid_until": entitlement.paid_until.isoformat() if entitlement and entitlement.paid_until else None,
        "token_version": user.token_version,
    }


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


@router.patch("/users/{user_id}", response_model=AdminUserRow)
async def update_user(
    user_id: str,
    payload: AdminUserUpdate,
    request: Request,
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> AdminUserRow:
    import uuid

    try:
        target_id = uuid.UUID(user_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid user id") from exc

    result = await db.execute(
        select(User, Entitlement)
        .outerjoin(Entitlement, Entitlement.user_id == User.id)
        .where(User.id == target_id)
    )
    row = result.first()
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    user, entitlement = row
    before = _state(user, entitlement)

    if payload.user_status is not None:
        try:
            new_status = UserStatus(payload.user_status)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail="Invalid user status") from exc
        if user.id == admin.id and new_status != UserStatus.ACTIVE:
            raise HTTPException(status_code=400, detail="You cannot suspend your own admin account")
        if user.status != new_status:
            user.status = new_status
            user.token_version += 1

    entitlement_fields_requested = any(
        value is not None
        for value in (
            payload.plan_code,
            payload.entitlement_status,
            payload.trial_ends_at,
            payload.paid_until,
        )
    )
    if entitlement is None and entitlement_fields_requested:
        entitlement = Entitlement(user_id=user.id)
        db.add(entitlement)
        await db.flush()

    if entitlement is not None:
        if payload.plan_code is not None:
            try:
                entitlement.plan_code = PlanCode(payload.plan_code)
            except ValueError as exc:
                raise HTTPException(status_code=400, detail="Invalid plan code") from exc
        if payload.entitlement_status is not None:
            try:
                entitlement.status = EntitlementStatus(payload.entitlement_status)
            except ValueError as exc:
                raise HTTPException(status_code=400, detail="Invalid entitlement status") from exc
        if "trial_ends_at" in payload.model_fields_set:
            entitlement.trial_ends_at = payload.trial_ends_at
        if "paid_until" in payload.model_fields_set:
            entitlement.paid_until = payload.paid_until

    after = _state(user, entitlement)
    if before == after:
        raise HTTPException(status_code=400, detail="No changes supplied")

    db.add(
        AdminActionLog(
            actor_admin_id=admin.id,
            target_user_id=user.id,
            action="user_access_updated",
            reason=payload.reason.strip(),
            before_state=before,
            after_state=after,
            ip_address=_request_ip(request),
            user_agent=_user_agent(request),
        )
    )
    db.add(
        SecurityAuditEvent(
            user_id=user.id,
            event_type="admin_access_change",
            description=f"Administrator changed account or plan access. Reason: {payload.reason.strip()}",
            ip_address=_request_ip(request),
            user_agent=_user_agent(request),
        )
    )
    await db.commit()

    return AdminUserRow(
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


@router.post("/users/{user_id}/revoke-sessions")
async def revoke_user_sessions(
    user_id: str,
    request: Request,
    reason: str = Query(min_length=3, max_length=300),
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    import uuid

    try:
        target_id = uuid.UUID(user_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid user id") from exc

    user = await db.scalar(select(User).where(User.id == target_id))
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    before = {"token_version": user.token_version}
    user.token_version += 1
    after = {"token_version": user.token_version}

    db.add(
        AdminActionLog(
            actor_admin_id=admin.id,
            target_user_id=user.id,
            action="sessions_revoked",
            reason=reason.strip(),
            before_state=before,
            after_state=after,
            ip_address=_request_ip(request),
            user_agent=_user_agent(request),
        )
    )
    db.add(
        SecurityAuditEvent(
            user_id=user.id,
            event_type="sessions_revoked_by_admin",
            description=f"All active sessions revoked by administrator. Reason: {reason.strip()}",
            ip_address=_request_ip(request),
            user_agent=_user_agent(request),
        )
    )
    await db.commit()
    return {"status": "ok"}


@router.get("/action-logs", response_model=list[AdminActionLogRow])
async def action_logs(
    limit: int = Query(default=200, ge=1, le=500),
    _: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> list[AdminActionLogRow]:
    actor = User.__table__.alias("actor")
    target = User.__table__.alias("target")
    rows = await db.execute(
        select(
            AdminActionLog,
            actor.c.email.label("actor_email"),
            target.c.email.label("target_email"),
        )
        .outerjoin(actor, actor.c.id == AdminActionLog.actor_admin_id)
        .outerjoin(target, target.c.id == AdminActionLog.target_user_id)
        .order_by(AdminActionLog.created_at.desc())
        .limit(limit)
    )
    return [
        AdminActionLogRow(
            id=str(log.id),
            actor_admin_id=str(log.actor_admin_id) if log.actor_admin_id else None,
            actor_admin_email=actor_email,
            target_user_id=str(log.target_user_id) if log.target_user_id else None,
            target_user_email=target_email,
            action=log.action,
            reason=log.reason,
            before_state=log.before_state,
            after_state=log.after_state,
            ip_address=log.ip_address,
            user_agent=log.user_agent,
            created_at=log.created_at,
        )
        for log, actor_email, target_email in rows.all()
    ]
