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
    BillingPlan,
    Entitlement,
    EntitlementStatus,
    PaymentRecord,
    PlanCode,
    SecurityAuditEvent,
    User,
    UserLocation,
    UserStatus,
)
from app.services.subscriptions import apply_manual_plan_change, normalize_paid_entitlement
from app.services.trials import normalize_entitlement
from app.services.email_delivery import EmailDeliveryError, send_test_email
from app.schemas.admin import (
    AdminActionLogRow,
    AdminBillingPlanCreate,
    AdminBillingPlanRow,
    AdminDeleteUserRequest,
    AdminAIUsageSummary,
    AdminOverview,
    AdminPaymentCreate,
    AdminPaymentRow,
    AdminSecurityEventRow,
    AdminSubscriptionSummary,
    AdminUserDetail,
    AdminUserLocationUpdate,
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
    unverified_users = await db.scalar(
        select(func.count(User.id)).where(User.email_verified.is_(False))
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
        unverified_users=unverified_users,
    )


@router.get("/users", response_model=list[AdminUserRow])
async def users(
    q: str | None = Query(default=None, max_length=120),
    limit: int = Query(default=200, ge=1, le=500),
    _: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> list[AdminUserRow]:
    statement = (
        select(User, Entitlement, BillingPlan)
        .outerjoin(Entitlement, Entitlement.user_id == User.id)
        .outerjoin(BillingPlan, BillingPlan.id == Entitlement.billing_plan_id)
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
            email_verified=user.email_verified,
            entitlement_status=entitlement.status.value if entitlement else None,
            plan_code=entitlement.plan_code.value if entitlement else None,
            billing_plan_id=str(entitlement.billing_plan_id) if entitlement and entitlement.billing_plan_id else None,
            billing_plan_name=billing_plan.name if billing_plan else None,
            trial_ends_at=entitlement.trial_ends_at if entitlement else None,
            paid_until=entitlement.paid_until if entitlement else None,
            created_at=user.created_at,
        )
        for user, entitlement, billing_plan in rows.all()
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
            payload.billing_plan_id,
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
        requested_plan = entitlement.plan_code
        requested_status = None

        if payload.plan_code is not None:
            try:
                requested_plan = PlanCode(payload.plan_code)
            except ValueError as exc:
                raise HTTPException(status_code=400, detail="Invalid plan code") from exc

        if payload.entitlement_status is not None:
            try:
                requested_status = EntitlementStatus(payload.entitlement_status)
            except ValueError as exc:
                raise HTTPException(status_code=400, detail="Invalid entitlement status") from exc

        selected_billing_plan = None
        if payload.billing_plan_id is not None:
            try:
                billing_plan_uuid = uuid.UUID(payload.billing_plan_id)
            except ValueError as exc:
                raise HTTPException(status_code=400, detail="Invalid billing plan id") from exc

            selected_billing_plan = await db.scalar(
                select(BillingPlan).where(
                    BillingPlan.id == billing_plan_uuid,
                    BillingPlan.is_active.is_(True),
                )
            )
            if selected_billing_plan is None:
                raise HTTPException(status_code=404, detail="Billing plan not found")

            entitlement.billing_plan_id = selected_billing_plan.id
            requested_plan = (
                PlanCode.PRO
                if selected_billing_plan.access_level == "pro"
                else PlanCode.FREE
            )

        if (
            payload.plan_code is not None
            or payload.entitlement_status is not None
            or selected_billing_plan is not None
        ):
            apply_manual_plan_change(
                entitlement,
                plan_code=requested_plan,
                entitlement_status=requested_status,
            )

        if "trial_ends_at" in payload.model_fields_set:
            entitlement.trial_ends_at = payload.trial_ends_at
        elif entitlement.status != EntitlementStatus.TRIAL:
            entitlement.trial_ends_at = None

        if "paid_until" in payload.model_fields_set:
            entitlement.paid_until = payload.paid_until
        elif (
            selected_billing_plan is not None
            and entitlement.status == EntitlementStatus.ACTIVE
            and entitlement.plan_code == PlanCode.PRO
        ):
            now = _utcnow()
            if selected_billing_plan.billing_period == "monthly":
                entitlement.paid_until = now + timedelta(days=30)
            elif selected_billing_plan.billing_period == "quarterly":
                entitlement.paid_until = now + timedelta(days=90)
            elif selected_billing_plan.billing_period == "yearly":
                entitlement.paid_until = now + timedelta(days=365)
            elif selected_billing_plan.billing_period == "lifetime":
                entitlement.paid_until = None

    if entitlement is not None:
        normalize_entitlement(entitlement)
        normalize_paid_entitlement(entitlement)

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
        email_verified=user.email_verified,
        entitlement_status=entitlement.status.value if entitlement else None,
        plan_code=entitlement.plan_code.value if entitlement else None,
        billing_plan_id=str(entitlement.billing_plan_id) if entitlement and entitlement.billing_plan_id else None,
        billing_plan_name=selected_billing_plan.name if entitlement and selected_billing_plan else None,
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



@router.post("/email/test")
async def test_email_delivery(
    request: Request,
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    try:
        await send_test_email(to_email=admin.email)
    except EmailDeliveryError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc

    db.add(
        SecurityAuditEvent(
            user_id=admin.id,
            event_type="email_delivery_test",
            description="Administrator sent a FinPilot email delivery test.",
            ip_address=_request_ip(request),
            user_agent=_user_agent(request),
        )
    )
    await db.commit()
    return {"status": "sent", "recipient": admin.email}


@router.get("/plans", response_model=list[AdminBillingPlanRow])
async def list_billing_plans(
    _: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> list[AdminBillingPlanRow]:
    rows = (await db.execute(select(BillingPlan).order_by(BillingPlan.created_at.desc()))).scalars().all()
    return [
        AdminBillingPlanRow(
            id=str(plan.id),
            code=plan.code,
            name=plan.name,
            access_level=plan.access_level,
            billing_period=plan.billing_period,
            google_play_product_id=plan.google_play_product_id,
            price=plan.price,
            currency=plan.currency,
            description=plan.description,
            features=plan.features,
            is_active=plan.is_active,
            created_at=plan.created_at,
            updated_at=plan.updated_at,
        )
        for plan in rows
    ]


@router.post("/plans", response_model=AdminBillingPlanRow, status_code=201)
async def create_billing_plan(
    payload: AdminBillingPlanCreate,
    request: Request,
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> AdminBillingPlanRow:
    existing = await db.scalar(select(BillingPlan.id).where(BillingPlan.code == payload.code.lower()))
    if existing:
        raise HTTPException(status_code=409, detail="Plan code already exists")

    plan = BillingPlan(
        code=payload.code.lower(),
        name=payload.name.strip(),
        access_level=payload.access_level,
        billing_period=payload.billing_period,
        google_play_product_id=payload.google_play_product_id.strip() if payload.google_play_product_id else None,
        price=payload.price,
        currency=payload.currency.upper(),
        description=payload.description.strip() if payload.description else None,
        features=payload.features,
        is_active=payload.is_active,
    )
    db.add(plan)
    await db.flush()
    db.add(
        AdminActionLog(
            actor_admin_id=admin.id,
            target_user_id=None,
            action="billing_plan_created",
            reason="Created billing plan",
            before_state=None,
            after_state={
                "id": str(plan.id),
                "code": plan.code,
                "name": plan.name,
                "access_level": plan.access_level,
                "billing_period": plan.billing_period,
                "google_play_product_id": plan.google_play_product_id,
                "price": str(plan.price),
                "currency": plan.currency,
            },
            ip_address=_request_ip(request),
            user_agent=_user_agent(request),
        )
    )
    await db.commit()
    await db.refresh(plan)
    return AdminBillingPlanRow(
        id=str(plan.id),
        code=plan.code,
        name=plan.name,
        access_level=plan.access_level,
        billing_period=plan.billing_period,
        google_play_product_id=plan.google_play_product_id,
        price=plan.price,
        currency=plan.currency,
        description=plan.description,
        features=plan.features,
        is_active=plan.is_active,
        created_at=plan.created_at,
        updated_at=plan.updated_at,
    )


@router.get("/payments", response_model=list[AdminPaymentRow])
async def list_payments(
    user_id: str | None = Query(default=None),
    limit: int = Query(default=200, ge=1, le=500),
    _: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> list[AdminPaymentRow]:
    recorder = User.__table__.alias("recorder")
    user_table = User.__table__.alias("payment_user")
    plan = BillingPlan.__table__.alias("payment_plan")
    statement = (
        select(
            PaymentRecord,
            user_table.c.email.label("user_email"),
            plan.c.name.label("plan_name"),
            recorder.c.email.label("recorder_email"),
        )
        .join(user_table, user_table.c.id == PaymentRecord.user_id)
        .outerjoin(plan, plan.c.id == PaymentRecord.billing_plan_id)
        .outerjoin(recorder, recorder.c.id == PaymentRecord.recorded_by_admin_id)
        .order_by(PaymentRecord.received_at.desc())
        .limit(limit)
    )
    if user_id:
        import uuid
        try:
            uid = uuid.UUID(user_id)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail="Invalid user id") from exc
        statement = statement.where(PaymentRecord.user_id == uid)

    rows = await db.execute(statement)
    return [
        AdminPaymentRow(
            id=str(payment.id),
            user_id=str(payment.user_id),
            user_email=user_email,
            billing_plan_id=str(payment.billing_plan_id) if payment.billing_plan_id else None,
            billing_plan_name=plan_name,
            amount=payment.amount,
            currency=payment.currency,
            payment_method=payment.payment_method,
            provider=payment.provider,
            reference=payment.reference,
            status=payment.status,
            notes=payment.notes,
            received_at=payment.received_at,
            recorded_by_admin_email=recorder_email,
            created_at=payment.created_at,
        )
        for payment, user_email, plan_name, recorder_email in rows.all()
    ]


@router.post("/payments", response_model=AdminPaymentRow, status_code=201)
async def record_payment(
    payload: AdminPaymentCreate,
    request: Request,
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> AdminPaymentRow:
    import uuid

    try:
        uid = uuid.UUID(payload.user_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid user id") from exc

    user = await db.scalar(select(User).where(User.id == uid))
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    plan = None
    plan_id = None
    if payload.billing_plan_id:
        try:
            plan_id = uuid.UUID(payload.billing_plan_id)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail="Invalid billing plan id") from exc
        plan = await db.scalar(select(BillingPlan).where(BillingPlan.id == plan_id))
        if not plan:
            raise HTTPException(status_code=404, detail="Billing plan not found")

    payment = PaymentRecord(
        user_id=user.id,
        billing_plan_id=plan_id,
        amount=payload.amount,
        currency=payload.currency.upper(),
        payment_method=payload.payment_method.strip(),
        provider=payload.provider.strip() if payload.provider else None,
        reference=payload.reference.strip() if payload.reference else None,
        status=payload.status,
        notes=payload.notes.strip() if payload.notes else None,
        received_at=payload.received_at,
        recorded_by_admin_id=admin.id,
    )
    db.add(payment)
    await db.flush()

    db.add(
        AdminActionLog(
            actor_admin_id=admin.id,
            target_user_id=user.id,
            action="payment_recorded",
            reason=payload.reason.strip(),
            before_state=None,
            after_state={
                "payment_id": str(payment.id),
                "amount": str(payment.amount),
                "currency": payment.currency,
                "method": payment.payment_method,
                "status": payment.status,
                "reference": payment.reference,
                "billing_plan_id": str(plan_id) if plan_id else None,
            },
            ip_address=_request_ip(request),
            user_agent=_user_agent(request),
        )
    )
    await db.commit()
    await db.refresh(payment)

    return AdminPaymentRow(
        id=str(payment.id),
        user_id=str(user.id),
        user_email=user.email,
        billing_plan_id=str(plan.id) if plan else None,
        billing_plan_name=plan.name if plan else None,
        amount=payment.amount,
        currency=payment.currency,
        payment_method=payment.payment_method,
        provider=payment.provider,
        reference=payment.reference,
        status=payment.status,
        notes=payment.notes,
        received_at=payment.received_at,
        recorded_by_admin_email=admin.email,
        created_at=payment.created_at,
    )


@router.get("/users/{user_id}/detail", response_model=AdminUserDetail)
async def user_detail(
    user_id: str,
    _: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> AdminUserDetail:
    import uuid
    try:
        uid = uuid.UUID(user_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid user id") from exc

    row = (await db.execute(
        select(User, Entitlement, UserLocation, BillingPlan)
        .outerjoin(Entitlement, Entitlement.user_id == User.id)
        .outerjoin(UserLocation, UserLocation.user_id == User.id)
        .outerjoin(BillingPlan, BillingPlan.id == Entitlement.billing_plan_id)
        .where(User.id == uid)
    )).first()
    if not row:
        raise HTTPException(status_code=404, detail="User not found")
    user, entitlement, location, billing_plan = row
    payments = await list_payments(user_id=str(user.id), limit=50, _=user, db=db)
    return AdminUserDetail(
        user=AdminUserRow(
            id=str(user.id),
            email=user.email,
            full_name=user.full_name,
            email_verified=user.email_verified,
            user_status=user.status.value,
            is_admin=user.is_admin,
            entitlement_status=entitlement.status.value if entitlement else None,
            plan_code=entitlement.plan_code.value if entitlement else None,
            trial_ends_at=entitlement.trial_ends_at if entitlement else None,
            paid_until=entitlement.paid_until if entitlement else None,
            created_at=user.created_at,
        ),
        country=location.country if location else None,
        state=location.state if location else None,
        city=location.city if location else None,
        postal_code=location.postal_code if location else None,
        last_ip_address=location.last_ip_address if location else None,
        last_user_agent=location.last_user_agent if location else None,
        location_updated_at=location.updated_at if location else None,
        payments=payments,
    )


@router.patch("/users/{user_id}/location")
async def update_user_location(
    user_id: str,
    payload: AdminUserLocationUpdate,
    request: Request,
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    import uuid
    try:
        uid = uuid.UUID(user_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid user id") from exc

    user = await db.scalar(select(User).where(User.id == uid))
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    location = await db.scalar(select(UserLocation).where(UserLocation.user_id == uid))
    before = {
        "country": location.country if location else None,
        "state": location.state if location else None,
        "city": location.city if location else None,
        "postal_code": location.postal_code if location else None,
    }
    if not location:
        location = UserLocation(user_id=uid)
        db.add(location)
    location.country = payload.country.strip() if payload.country else None
    location.state = payload.state.strip() if payload.state else None
    location.city = payload.city.strip() if payload.city else None
    location.postal_code = payload.postal_code.strip() if payload.postal_code else None

    after = {
        "country": location.country,
        "state": location.state,
        "city": location.city,
        "postal_code": location.postal_code,
    }
    db.add(
        AdminActionLog(
            actor_admin_id=admin.id,
            target_user_id=uid,
            action="user_location_updated",
            reason=payload.reason.strip(),
            before_state=before,
            after_state=after,
            ip_address=_request_ip(request),
            user_agent=_user_agent(request),
        )
    )
    await db.commit()
    return {"status": "ok"}


@router.post("/users/{user_id}/delete")
async def delete_user_account(
    user_id: str,
    payload: AdminDeleteUserRequest,
    request: Request,
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    import uuid
    try:
        uid = uuid.UUID(user_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid user id") from exc

    user = await db.scalar(select(User).where(User.id == uid))
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user.id == admin.id:
        raise HTTPException(status_code=400, detail="You cannot delete your own admin account")
    if user.is_admin:
        raise HTTPException(status_code=400, detail="Another admin account cannot be deleted here")

    before = {"status": user.status.value, "token_version": user.token_version}
    user.status = UserStatus.DELETED
    user.token_version += 1
    after = {"status": user.status.value, "token_version": user.token_version}

    db.add(
        AdminActionLog(
            actor_admin_id=admin.id,
            target_user_id=user.id,
            action="user_deleted",
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
            event_type="account_deleted_by_admin",
            description=f"Account disabled/deleted by administrator. Reason: {payload.reason.strip()}",
            ip_address=_request_ip(request),
            user_agent=_user_agent(request),
        )
    )
    await db.commit()
    return {"status": "deleted"}
