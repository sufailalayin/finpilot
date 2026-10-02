import csv
import io
import math
import uuid
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response, status
from sqlalchemy import case, distinct, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.request_meta import client_ip, user_agent
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
    RefreshSession,
    SecurityAuditEvent,
    User,
    UserLocation,
    UserStatus,
)
from app.services.email_delivery import EmailDeliveryError, send_test_email
from app.services.subscriptions import apply_manual_plan_change, normalize_paid_entitlement
from app.services.trials import normalize_entitlement
from app.schemas.admin import (
    AdminActionLogRow,
    AdminAIUsageSummary,
    AdminAnalyticsAI,
    AdminAnalyticsOverview,
    AdminAnalyticsRevenue,
    AdminAnalyticsSecurity,
    AdminAnalyticsSubscriptions,
    AdminAnalyticsUsers,
    AdminBillingPlanCreate,
    AdminBillingPlanRow,
    AdminBillingPlanUpdate,
    AdminDeleteUserRequest,
    AdminOverview,
    AdminPaginatedActionLogs,
    AdminPaginatedPayments,
    AdminPaginatedSecurityEvents,
    AdminPaginatedUsers,
    AdminPaginationMeta,
    AdminPaymentCreate,
    AdminPaymentRow,
    AdminPaymentUpdate,
    AdminPaymentVoidRequest,
    AdminSecurityEventRow,
    AdminSubscriptionSummary,
    AdminUserDetail,
    AdminUserFinancialSummary,
    AdminUserLocationUpdate,
    AdminUserRow,
    AdminUserUpdate,
    AIUsagePoint,
    AITopUser,
    AppReleaseResponse,
    AppReleaseUpdate,
    PaymentMethodDistributionItem,
    PlanDistributionItem,
    RevenuePoint,
    SecurityBreakdownItem,
    SecurityTrendPoint,
    TrialConversionMetrics,
    UserGrowthPoint,
)

router = APIRouter(prefix="/admin", tags=["admin"])


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _state(user: User, entitlement: Entitlement | None) -> dict:
    return {
        "user_status": user.status.value,
        "full_name": user.full_name,
        "plan_code": entitlement.plan_code.value if entitlement else None,
        "billing_plan_id": str(entitlement.billing_plan_id) if entitlement and entitlement.billing_plan_id else None,
        "entitlement_status": entitlement.status.value if entitlement else None,
        "trial_ends_at": entitlement.trial_ends_at.isoformat() if entitlement and entitlement.trial_ends_at else None,
        "paid_until": entitlement.paid_until.isoformat() if entitlement and entitlement.paid_until else None,
        "token_version": user.token_version,
    }


# ==============================================================================
# 1. ANALYTICS APIS
# ==============================================================================

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


@router.get("/analytics/overview", response_model=AdminAnalyticsOverview)
async def analytics_overview(
    _: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> AdminAnalyticsOverview:
    now = _utcnow()
    today_start = datetime(now.year, now.month, now.day, tzinfo=timezone.utc)
    month_start = datetime(now.year, now.month, 1, tzinfo=timezone.utc)
    year_start = datetime(now.year, 1, 1, tzinfo=timezone.utc)
    seven_days_ago = now - timedelta(days=7)
    thirty_days_ago = now - timedelta(days=30)
    day_ago = now - timedelta(hours=24)

    total_users = await db.scalar(select(func.count(User.id))) or 0
    active_users = await db.scalar(
        select(func.count(User.id)).where(User.status == UserStatus.ACTIVE)
    ) or 0
    new_users_today = await db.scalar(
        select(func.count(User.id)).where(User.created_at >= today_start)
    ) or 0
    new_users_7d = await db.scalar(
        select(func.count(User.id)).where(User.created_at >= seven_days_ago)
    ) or 0
    new_users_30d = await db.scalar(
        select(func.count(User.id)).where(User.created_at >= thirty_days_ago)
    ) or 0
    active_trials = await db.scalar(
        select(func.count(Entitlement.id)).where(Entitlement.status == EntitlementStatus.TRIAL)
    ) or 0
    paid_users = await db.scalar(
        select(func.count(Entitlement.id)).where(
            Entitlement.plan_code == PlanCode.PRO,
            Entitlement.status == EntitlementStatus.ACTIVE,
        )
    ) or 0
    free_users = await db.scalar(
        select(func.count(Entitlement.id)).where(Entitlement.plan_code == PlanCode.FREE)
    ) or 0
    expired_users = await db.scalar(
        select(func.count(Entitlement.id)).where(Entitlement.status == EntitlementStatus.EXPIRED)
    ) or 0
    suspended_users = await db.scalar(
        select(func.count(User.id)).where(User.status == UserStatus.SUSPENDED)
    ) or 0

    revenue_today = await db.scalar(
        select(func.coalesce(func.sum(PaymentRecord.amount), Decimal("0.00")))
        .where(PaymentRecord.status == "received", PaymentRecord.received_at >= today_start)
    ) or Decimal("0.00")

    revenue_this_month = await db.scalar(
        select(func.coalesce(func.sum(PaymentRecord.amount), Decimal("0.00")))
        .where(PaymentRecord.status == "received", PaymentRecord.received_at >= month_start)
    ) or Decimal("0.00")

    revenue_this_year = await db.scalar(
        select(func.coalesce(func.sum(PaymentRecord.amount), Decimal("0.00")))
        .where(PaymentRecord.status == "received", PaymentRecord.received_at >= year_start)
    ) or Decimal("0.00")

    total_recorded_revenue = await db.scalar(
        select(func.coalesce(func.sum(PaymentRecord.amount), Decimal("0.00")))
        .where(PaymentRecord.status == "received")
    ) or Decimal("0.00")

    ai_requests_today = await db.scalar(
        select(func.count(AIUsageEvent.id)).where(AIUsageEvent.created_at >= today_start)
    ) or 0
    ai_requests_7d = await db.scalar(
        select(func.count(AIUsageEvent.id)).where(AIUsageEvent.created_at >= seven_days_ago)
    ) or 0

    security_events_24h = await db.scalar(
        select(func.count(SecurityAuditEvent.id)).where(SecurityAuditEvent.created_at >= day_ago)
    ) or 0
    failed_login_attempts = await db.scalar(
        select(func.coalesce(func.sum(User.failed_login_attempts), 0))
    ) or 0
    unverified_emails = await db.scalar(
        select(func.count(User.id)).where(User.email_verified.is_(False))
    ) or 0

    finance_accounts = await db.scalar(select(func.count(FinanceAccount.id))) or 0
    transactions = await db.scalar(select(func.count(Transaction.id))) or 0

    return AdminAnalyticsOverview(
        total_users=total_users,
        active_users=active_users,
        new_users_today=new_users_today,
        new_users_7d=new_users_7d,
        new_users_30d=new_users_30d,
        active_trials=active_trials,
        paid_users=paid_users,
        free_users=free_users,
        expired_users=expired_users,
        suspended_users=suspended_users,
        revenue_today=revenue_today,
        revenue_this_month=revenue_this_month,
        revenue_this_year=revenue_this_year,
        total_recorded_revenue=total_recorded_revenue,
        ai_requests_today=ai_requests_today,
        ai_requests_7d=ai_requests_7d,
        security_events_24h=security_events_24h,
        failed_login_attempts=int(failed_login_attempts),
        unverified_emails=unverified_emails,
        finance_accounts=finance_accounts,
        transactions=transactions,
    )


@router.get("/analytics/users", response_model=AdminAnalyticsUsers)
async def analytics_users(
    period: str = Query(default="30d", pattern=r"^(7d|30d|90d|180d|365d|all)$"),
    _: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> AdminAnalyticsUsers:
    now = _utcnow()
    days_map = {"7d": 7, "30d": 30, "90d": 90, "180d": 180, "365d": 365}

    if period == "all":
        earliest = await db.scalar(select(func.min(User.created_at)))
        start_date = (earliest or now).date()
    else:
        days = days_map.get(period, 30)
        start_date = (now - timedelta(days=days - 1)).date()

    prior_count = await db.scalar(
        select(func.count(User.id)).where(func.date(User.created_at) < start_date)
    ) or 0

    rows = (
        await db.execute(
            select(
                func.date(User.created_at).label("reg_date"),
                func.count(User.id).label("count"),
            )
            .where(func.date(User.created_at) >= start_date)
            .group_by(func.date(User.created_at))
            .order_by(func.date(User.created_at).asc())
        )
    ).all()

    counts_by_date = {row.reg_date: row.count for row in rows}

    points: list[UserGrowthPoint] = []
    cumulative = prior_count
    current = start_date
    end_date = now.date()

    total_reg = 0
    while current <= end_date:
        cnt = counts_by_date.get(current, 0)
        total_reg += cnt
        cumulative += cnt
        points.append(
            UserGrowthPoint(
                date=current.isoformat(),
                registrations=cnt,
                cumulative=cumulative,
            )
        )
        current += timedelta(days=1)

    return AdminAnalyticsUsers(
        period=period,
        points=points,
        total_registrations=total_reg,
    )


@router.get("/analytics/revenue", response_model=AdminAnalyticsRevenue)
async def analytics_revenue(
    period: str = Query(default="daily", pattern=r"^(daily|weekly|monthly|yearly)$"),
    _: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> AdminAnalyticsRevenue:
    now = _utcnow()

    if period == "daily":
        start_date = (now - timedelta(days=29)).date()
        date_col = func.date(PaymentRecord.received_at)
    elif period == "weekly":
        start_date = (now - timedelta(weeks=12)).date()
        date_col = func.date_trunc("week", PaymentRecord.received_at)
    elif period == "yearly":
        start_date = date(now.year - 4, 1, 1)
        date_col = func.date_trunc("year", PaymentRecord.received_at)
    else:  # monthly
        start_date = (now.replace(day=1) - timedelta(days=365)).replace(day=1).date()
        date_col = func.date_trunc("month", PaymentRecord.received_at)

    rows = (
        await db.execute(
            select(
                date_col.label("bucket"),
                func.coalesce(
                    func.sum(
                        case(
                            (PaymentRecord.status == "received", PaymentRecord.amount),
                            else_=Decimal("0.00"),
                        )
                    ),
                    Decimal("0.00"),
                ).label("revenue"),
                func.count(
                    case((PaymentRecord.status == "received", 1))
                ).label("count"),
                func.coalesce(
                    func.sum(
                        case(
                            (PaymentRecord.status == "voided", PaymentRecord.amount),
                            (PaymentRecord.status == "refunded", PaymentRecord.amount),
                            else_=Decimal("0.00"),
                        )
                    ),
                    Decimal("0.00"),
                ).label("voided"),
            )
            .where(func.date(PaymentRecord.received_at) >= start_date)
            .group_by(date_col)
            .order_by(date_col.asc())
        )
    ).all()

    points: list[RevenuePoint] = []
    total_rev = Decimal("0.00")
    total_tx = 0
    total_void = Decimal("0.00")

    for r in rows:
        bucket_val = r.bucket
        if isinstance(bucket_val, datetime):
            b_str = bucket_val.strftime("%Y-%m-%d" if period != "monthly" else "%Y-%m")
        elif isinstance(bucket_val, date):
            b_str = bucket_val.isoformat()
        else:
            b_str = str(bucket_val)

        points.append(
            RevenuePoint(
                date=b_str,
                revenue=r.revenue,
                count=r.count,
                voided_amount=r.voided,
            )
        )
        total_rev += r.revenue
        total_tx += r.count
        total_void += r.voided

    return AdminAnalyticsRevenue(
        period=period,
        points=points,
        total_revenue=total_rev,
        total_transactions=total_tx,
        voided_revenue=total_void,
    )


@router.get("/analytics/subscriptions", response_model=AdminAnalyticsSubscriptions)
async def analytics_subscriptions(
    _: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> AdminAnalyticsSubscriptions:
    free_cnt = await db.scalar(
        select(func.count(Entitlement.id)).where(Entitlement.plan_code == PlanCode.FREE)
    ) or 0
    trial_cnt = await db.scalar(
        select(func.count(Entitlement.id)).where(Entitlement.status == EntitlementStatus.TRIAL)
    ) or 0
    active_paid_cnt = await db.scalar(
        select(func.count(Entitlement.id)).where(
            Entitlement.plan_code == PlanCode.PRO,
            Entitlement.status == EntitlementStatus.ACTIVE,
        )
    ) or 0
    expired_cnt = await db.scalar(
        select(func.count(Entitlement.id)).where(Entitlement.status == EntitlementStatus.EXPIRED)
    ) or 0
    cancelled_cnt = await db.scalar(
        select(func.count(Entitlement.id)).where(Entitlement.status == EntitlementStatus.CANCELLED)
    ) or 0
    suspended_cnt = await db.scalar(
        select(func.count(User.id)).where(User.status == UserStatus.SUSPENDED)
    ) or 0

    total_subscribers = free_cnt + trial_cnt + active_paid_cnt + expired_cnt + cancelled_cnt

    # Plan Distribution
    plan_rows = (
        await db.execute(
            select(
                BillingPlan.id,
                BillingPlan.code,
                BillingPlan.name,
                func.count(Entitlement.id).label("users_count"),
            )
            .outerjoin(Entitlement, Entitlement.billing_plan_id == BillingPlan.id)
            .group_by(BillingPlan.id, BillingPlan.code, BillingPlan.name)
            .order_by(func.count(Entitlement.id).desc())
        )
    ).all()

    by_plan: list[PlanDistributionItem] = []
    accounted_in_plans = 0
    for p in plan_rows:
        cnt = p.users_count or 0
        accounted_in_plans += cnt
        pct = (cnt / total_subscribers * 100) if total_subscribers > 0 else 0.0
        by_plan.append(
            PlanDistributionItem(
                plan_id=str(p.id),
                plan_code=p.code,
                plan_name=p.name,
                count=cnt,
                percentage=round(pct, 1),
            )
        )

    remaining_free = max(0, free_cnt)
    if remaining_free > 0:
        pct = (remaining_free / total_subscribers * 100) if total_subscribers > 0 else 0.0
        by_plan.append(
            PlanDistributionItem(
                plan_id=None,
                plan_code="free_standard",
                plan_name="Free Standard",
                count=remaining_free,
                percentage=round(pct, 1),
            )
        )

    # Trial Conversion
    trials_started = await db.scalar(
        select(func.count(Entitlement.id)).where(
            or_(
                Entitlement.trial_started_at.is_not(None),
                Entitlement.status == EntitlementStatus.TRIAL,
                Entitlement.status == EntitlementStatus.EXPIRED,
            )
        )
    ) or 0
    trials_active = trial_cnt
    trials_converted = active_paid_cnt
    trials_expired = expired_cnt
    conv_rate = (
        (trials_converted / max(trials_started, 1) * 100)
        if trials_started > 0
        else 0.0
    )

    # Payment Methods
    method_rows = (
        await db.execute(
            select(
                PaymentRecord.payment_method,
                func.count(PaymentRecord.id).label("count"),
                func.sum(PaymentRecord.amount).label("amount"),
            )
            .where(PaymentRecord.status == "received")
            .group_by(PaymentRecord.payment_method)
            .order_by(func.sum(PaymentRecord.amount).desc())
        )
    ).all()

    total_payments_amount = sum((m.amount for m in method_rows), Decimal("0.00"))
    payment_methods = [
        PaymentMethodDistributionItem(
            method=m.payment_method or "other",
            count=m.count,
            amount=m.amount or Decimal("0.00"),
            percentage=round(
                float((m.amount / total_payments_amount) * 100)
                if total_payments_amount > 0
                else 0.0,
                1,
            ),
        )
        for m in method_rows
    ]

    return AdminAnalyticsSubscriptions(
        distribution={
            "trial": trial_cnt,
            "free": free_cnt,
            "active_paid": active_paid_cnt,
            "expired": expired_cnt,
            "cancelled": cancelled_cnt,
            "suspended": suspended_cnt,
        },
        by_plan=by_plan,
        trial_conversion=TrialConversionMetrics(
            trials_started=trials_started,
            trials_active=trials_active,
            trials_converted=trials_converted,
            trials_expired=trials_expired,
            conversion_rate_pct=round(conv_rate, 1),
        ),
        payment_methods=payment_methods,
    )


@router.get("/analytics/ai", response_model=AdminAnalyticsAI)
async def analytics_ai(
    _: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> AdminAnalyticsAI:
    now = _utcnow()
    thirty_days_ago = now - timedelta(days=30)
    seven_days_ago = now - timedelta(days=7)
    day_ago = now - timedelta(hours=24)

    total_requests = await db.scalar(select(func.count(AIUsageEvent.id))) or 0
    requests_24h = await db.scalar(
        select(func.count(AIUsageEvent.id)).where(AIUsageEvent.created_at >= day_ago)
    ) or 0
    requests_7d = await db.scalar(
        select(func.count(AIUsageEvent.id)).where(AIUsageEvent.created_at >= seven_days_ago)
    ) or 0
    requests_30d = await db.scalar(
        select(func.count(AIUsageEvent.id)).where(AIUsageEvent.created_at >= thirty_days_ago)
    ) or 0
    unique_users_7d = await db.scalar(
        select(func.count(distinct(AIUsageEvent.user_id))).where(
            AIUsageEvent.created_at >= seven_days_ago
        )
    ) or 0

    points_rows = (
        await db.execute(
            select(
                func.date(AIUsageEvent.created_at).label("d"),
                func.count(AIUsageEvent.id).label("reqs"),
                func.coalesce(func.sum(AIUsageEvent.prompt_chars), 0).label("prompt"),
                func.coalesce(func.sum(AIUsageEvent.response_chars), 0).label("resp"),
            )
            .where(AIUsageEvent.created_at >= thirty_days_ago)
            .group_by(func.date(AIUsageEvent.created_at))
            .order_by(func.date(AIUsageEvent.created_at).asc())
        )
    ).all()

    points = [
        AIUsagePoint(
            date=row.d.isoformat() if isinstance(row.d, date) else str(row.d),
            requests=row.reqs,
            prompt_chars=int(row.prompt),
            response_chars=int(row.resp),
        )
        for row in points_rows
    ]

    top_user_rows = (
        await db.execute(
            select(
                User.id,
                User.email,
                func.count(AIUsageEvent.id).label("reqs"),
            )
            .join(AIUsageEvent, AIUsageEvent.user_id == User.id)
            .where(AIUsageEvent.created_at >= thirty_days_ago)
            .group_by(User.id, User.email)
            .order_by(func.count(AIUsageEvent.id).desc())
            .limit(10)
        )
    ).all()

    top_users = [
        AITopUser(
            user_id=str(row.id),
            user_email=row.email,
            requests=row.reqs,
        )
        for row in top_user_rows
    ]

    return AdminAnalyticsAI(
        total_requests=total_requests,
        requests_24h=requests_24h,
        requests_7d=requests_7d,
        requests_30d=requests_30d,
        unique_users_7d=unique_users_7d,
        points=points,
        top_users=top_users,
    )


@router.get("/analytics/security", response_model=AdminAnalyticsSecurity)
async def analytics_security(
    period: str = Query(default="7d", pattern=r"^(24h|7d|30d)$"),
    _: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> AdminAnalyticsSecurity:
    now = _utcnow()
    if period == "24h":
        start_time = now - timedelta(hours=24)
    elif period == "30d":
        start_time = now - timedelta(days=30)
    else:
        start_time = now - timedelta(days=7)

    total_events = await db.scalar(
        select(func.count(SecurityAuditEvent.id)).where(
            SecurityAuditEvent.created_at >= start_time
        )
    ) or 0

    failed_logins = await db.scalar(
        select(func.count(SecurityAuditEvent.id)).where(
            SecurityAuditEvent.created_at >= start_time,
            or_(
                SecurityAuditEvent.event_type.ilike("%fail%"),
                SecurityAuditEvent.event_type.ilike("%lock%"),
            ),
        )
    ) or 0

    breakdown_rows = (
        await db.execute(
            select(
                SecurityAuditEvent.event_type,
                func.count(SecurityAuditEvent.id).label("count"),
            )
            .where(SecurityAuditEvent.created_at >= start_time)
            .group_by(SecurityAuditEvent.event_type)
            .order_by(func.count(SecurityAuditEvent.id).desc())
            .limit(10)
        )
    ).all()

    breakdown = [
        SecurityBreakdownItem(event_type=row.event_type, count=row.count)
        for row in breakdown_rows
    ]

    trend_rows = (
        await db.execute(
            select(
                func.date(SecurityAuditEvent.created_at).label("d"),
                func.count(SecurityAuditEvent.id).label("total"),
                func.count(
                    case((SecurityAuditEvent.event_type.ilike("%login%"), 1))
                ).label("logins"),
                func.count(
                    case((SecurityAuditEvent.event_type.ilike("%fail%"), 1))
                ).label("failures"),
            )
            .where(SecurityAuditEvent.created_at >= start_time)
            .group_by(func.date(SecurityAuditEvent.created_at))
            .order_by(func.date(SecurityAuditEvent.created_at).asc())
        )
    ).all()

    points = [
        SecurityTrendPoint(
            date=row.d.isoformat() if isinstance(row.d, date) else str(row.d),
            total=row.total,
            logins=row.logins,
            failures=row.failures,
        )
        for row in trend_rows
    ]

    return AdminAnalyticsSecurity(
        period=period,
        total_events=total_events,
        failed_logins=failed_logins,
        breakdown=breakdown,
        points=points,
    )


# ==============================================================================
# 2. USER MANAGEMENT APIS (WITH SERVER-SIDE PAGINATION & ACTIONS)
# ==============================================================================

@router.get("/users", response_model=AdminPaginatedUsers)
async def list_users(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=200),
    q: str | None = Query(default=None, max_length=120),
    status: str | None = Query(default=None),
    plan: str | None = Query(default=None),
    subscription_status: str | None = Query(default=None),
    sort_by: str = Query(default="created_at", pattern=r"^(created_at|email|full_name|user_status)$"),
    sort_order: str = Query(default="desc", pattern=r"^(asc|desc)$"),
    _: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> AdminPaginatedUsers:
    base_query = (
        select(User, Entitlement, BillingPlan)
        .outerjoin(Entitlement, Entitlement.user_id == User.id)
        .outerjoin(BillingPlan, BillingPlan.id == Entitlement.billing_plan_id)
    )

    if q:
        term = f"%{q.strip()}%"
        base_query = base_query.where(
            or_(
                User.email.ilike(term),
                User.full_name.ilike(term),
                func.cast(User.id, String).ilike(term),
            )
        )

    if status:
        base_query = base_query.where(User.status == status)

    if plan:
        base_query = base_query.where(Entitlement.plan_code == plan)

    if subscription_status:
        base_query = base_query.where(Entitlement.status == subscription_status)

    # Count total
    count_stmt = select(func.count(distinct(User.id))).select_from(base_query.subquery())
    total = await db.scalar(count_stmt) or 0

    # Sorting
    order_col = getattr(User, sort_by, User.created_at)
    if sort_order == "desc":
        base_query = base_query.order_by(order_col.desc())
    else:
        base_query = base_query.order_by(order_col.asc())

    offset = (page - 1) * page_size
    base_query = base_query.offset(offset).limit(page_size)

    rows = await db.execute(base_query)
    items = [
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

    total_pages = max(1, math.ceil(total / page_size))

    return AdminPaginatedUsers(
        items=items,
        meta=AdminPaginationMeta(
            page=page,
            page_size=page_size,
            total=total,
            total_pages=total_pages,
        ),
    )


@router.get("/users/{user_id}/detail", response_model=AdminUserDetail)
async def user_detail(
    user_id: str,
    _: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> AdminUserDetail:
    try:
        uid = uuid.UUID(user_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid user id") from exc

    row = (
        await db.execute(
            select(User, Entitlement, UserLocation, BillingPlan)
            .outerjoin(Entitlement, Entitlement.user_id == User.id)
            .outerjoin(UserLocation, UserLocation.user_id == User.id)
            .outerjoin(BillingPlan, BillingPlan.id == Entitlement.billing_plan_id)
            .where(User.id == uid)
        )
    ).first()

    if not row:
        raise HTTPException(status_code=404, detail="User not found")

    user, entitlement, location, billing_plan = row

    # Fetch user payments
    payments_result = await db.execute(
        select(PaymentRecord, BillingPlan.name.label("plan_name"))
        .outerjoin(BillingPlan, BillingPlan.id == PaymentRecord.billing_plan_id)
        .where(PaymentRecord.user_id == user.id)
        .order_by(PaymentRecord.received_at.desc())
        .limit(50)
    )
    payments = [
        AdminPaymentRow(
            id=str(payment.id),
            user_id=str(payment.user_id),
            user_email=user.email,
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
            recorded_by_admin_email=None,
            created_at=payment.created_at,
        )
        for payment, plan_name in payments_result.all()
    ]

    # Safe financial summary (counts only)
    accounts_count = await db.scalar(
        select(func.count(FinanceAccount.id)).where(FinanceAccount.user_id == user.id)
    ) or 0
    tx_count = await db.scalar(
        select(func.count(Transaction.id)).where(Transaction.user_id == user.id)
    ) or 0
    assets_count = await db.scalar(
        select(func.count(Asset.id)).where(Asset.user_id == user.id)
    ) or 0
    liabilities_count = await db.scalar(
        select(func.count(Liability.id)).where(Liability.user_id == user.id)
    ) or 0
    last_tx_date = await db.scalar(
        select(func.max(Transaction.created_at)).where(Transaction.user_id == user.id)
    )

    financial_summary = AdminUserFinancialSummary(
        accounts_count=accounts_count,
        transactions_count=tx_count,
        assets_count=assets_count,
        liabilities_count=liabilities_count,
        last_activity_date=last_tx_date,
    )

    # Recent security events for this user
    sec_events = (
        await db.execute(
            select(SecurityAuditEvent)
            .where(SecurityAuditEvent.user_id == user.id)
            .order_by(SecurityAuditEvent.created_at.desc())
            .limit(20)
        )
    ).scalars().all()
    recent_sec = [
        AdminSecurityEventRow(
            id=str(ev.id),
            user_id=str(ev.user_id),
            user_email=user.email,
            event_type=ev.event_type,
            description=ev.description,
            ip_address=ev.ip_address,
            user_agent=ev.user_agent,
            created_at=ev.created_at,
        )
        for ev in sec_events
    ]

    # Recent admin actions targeting this user
    admin_actions = (
        await db.execute(
            select(AdminActionLog, User.email.label("actor_email"))
            .outerjoin(User, User.id == AdminActionLog.actor_admin_id)
            .where(AdminActionLog.target_user_id == user.id)
            .order_by(AdminActionLog.created_at.desc())
            .limit(20)
        )
    ).all()
    recent_actions = [
        AdminActionLogRow(
            id=str(log.id),
            actor_admin_id=str(log.actor_admin_id) if log.actor_admin_id else None,
            actor_admin_email=actor_email,
            target_user_id=str(log.target_user_id),
            target_user_email=user.email,
            action=log.action,
            reason=log.reason,
            before_state=log.before_state,
            after_state=log.after_state,
            ip_address=log.ip_address,
            user_agent=log.user_agent,
            created_at=log.created_at,
        )
        for log, actor_email in admin_actions
    ]

    # Active sessions count
    now = _utcnow()
    active_sessions = await db.scalar(
        select(func.count(RefreshSession.id)).where(
            RefreshSession.user_id == user.id,
            RefreshSession.revoked_at.is_(None),
            RefreshSession.expires_at > now,
        )
    ) or 0

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
            billing_plan_id=str(entitlement.billing_plan_id) if entitlement and entitlement.billing_plan_id else None,
            billing_plan_name=billing_plan.name if billing_plan else None,
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
        financial_summary=financial_summary,
        recent_security_events=recent_sec,
        recent_admin_actions=recent_actions,
        active_sessions_count=active_sessions,
    )


@router.patch("/users/{user_id}", response_model=AdminUserRow)
async def update_user(
    user_id: str,
    payload: AdminUserUpdate,
    request: Request,
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> AdminUserRow:
    try:
        target_id = uuid.UUID(user_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid user id") from exc

    result = await db.execute(
        select(User, Entitlement)
        .outerjoin(Entitlement, Entitlement.user_id == User.id)
        .where(User.id == target_id)
    )
    row = result.first()
    if row is None:
        raise HTTPException(status_code=404, detail="User not found")

    user, entitlement = row
    before = _state(user, entitlement)

    if payload.full_name is not None:
        user.full_name = payload.full_name.strip() or None

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
        billing_plan_field_requested = "billing_plan_id" in payload.model_fields_set
        if billing_plan_field_requested:
            if payload.billing_plan_id:
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
            else:
                entitlement.billing_plan_id = None

        if (
            payload.plan_code is not None
            or payload.entitlement_status is not None
            or billing_plan_field_requested
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

    current_billing_plan = selected_billing_plan if entitlement is not None else None
    if entitlement is not None:
        normalize_entitlement(entitlement)
        normalize_paid_entitlement(entitlement)
        if entitlement.billing_plan_id and current_billing_plan is None:
            current_billing_plan = await db.scalar(
                select(BillingPlan).where(BillingPlan.id == entitlement.billing_plan_id)
            )

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
            ip_address=client_ip(request),
            user_agent=user_agent(request),
        )
    )
    db.add(
        SecurityAuditEvent(
            user_id=user.id,
            event_type="admin_access_change",
            description=f"Administrator changed account or plan access. Reason: {payload.reason.strip()}",
            ip_address=client_ip(request),
            user_agent=user_agent(request),
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
        billing_plan_name=current_billing_plan.name if entitlement and current_billing_plan else None,
        trial_ends_at=entitlement.trial_ends_at if entitlement else None,
        paid_until=entitlement.paid_until if entitlement else None,
        created_at=user.created_at,
    )


@router.post("/users/{user_id}/suspend")
async def suspend_user(
    user_id: str,
    request: Request,
    reason: str = Query(min_length=3, max_length=300),
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    try:
        uid = uuid.UUID(user_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid user id") from exc

    user = await db.scalar(select(User).where(User.id == uid))
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user.id == admin.id:
        raise HTTPException(status_code=400, detail="You cannot suspend your own admin account")

    before = {"status": user.status.value, "token_version": user.token_version}
    user.status = UserStatus.SUSPENDED
    user.token_version += 1
    after = {"status": user.status.value, "token_version": user.token_version}

    # Revoke all active refresh sessions
    now = _utcnow()
    sessions = (await db.execute(
        select(RefreshSession).where(
            RefreshSession.user_id == user.id,
            RefreshSession.revoked_at.is_(None),
        )
    )).scalars().all()
    for s in sessions:
        s.revoked_at = now

    db.add(
        AdminActionLog(
            actor_admin_id=admin.id,
            target_user_id=user.id,
            action="user_suspended",
            reason=reason.strip(),
            before_state=before,
            after_state=after,
            ip_address=client_ip(request),
            user_agent=user_agent(request),
        )
    )
    db.add(
        SecurityAuditEvent(
            user_id=user.id,
            event_type="user_suspended_by_admin",
            description=f"Account suspended by administrator. Reason: {reason.strip()}",
            ip_address=client_ip(request),
            user_agent=user_agent(request),
        )
    )
    await db.commit()
    return {"status": "suspended"}


@router.post("/users/{user_id}/restore")
async def restore_user(
    user_id: str,
    request: Request,
    reason: str = Query(min_length=3, max_length=300),
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    try:
        uid = uuid.UUID(user_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid user id") from exc

    user = await db.scalar(select(User).where(User.id == uid))
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    before = {"status": user.status.value, "failed_login_attempts": user.failed_login_attempts}
    user.status = UserStatus.ACTIVE
    user.failed_login_attempts = 0
    user.login_locked_until = None
    after = {"status": user.status.value, "failed_login_attempts": user.failed_login_attempts}

    db.add(
        AdminActionLog(
            actor_admin_id=admin.id,
            target_user_id=user.id,
            action="user_restored",
            reason=reason.strip(),
            before_state=before,
            after_state=after,
            ip_address=client_ip(request),
            user_agent=user_agent(request),
        )
    )
    db.add(
        SecurityAuditEvent(
            user_id=user.id,
            event_type="user_restored_by_admin",
            description=f"Account restored by administrator. Reason: {reason.strip()}",
            ip_address=client_ip(request),
            user_agent=user_agent(request),
        )
    )
    await db.commit()
    return {"status": "active"}


@router.post("/users/{user_id}/revoke-sessions")
async def revoke_user_sessions(
    user_id: str,
    request: Request,
    reason: str = Query(min_length=3, max_length=300),
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
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

    now = _utcnow()
    sessions = (await db.execute(
        select(RefreshSession).where(
            RefreshSession.user_id == user.id,
            RefreshSession.revoked_at.is_(None),
        )
    )).scalars().all()
    for s in sessions:
        s.revoked_at = now

    db.add(
        AdminActionLog(
            actor_admin_id=admin.id,
            target_user_id=user.id,
            action="sessions_revoked",
            reason=reason.strip(),
            before_state=before,
            after_state=after,
            ip_address=client_ip(request),
            user_agent=user_agent(request),
        )
    )
    db.add(
        SecurityAuditEvent(
            user_id=user.id,
            event_type="sessions_revoked_by_admin",
            description=f"All active sessions revoked by administrator. Reason: {reason.strip()}",
            ip_address=client_ip(request),
            user_agent=user_agent(request),
        )
    )
    await db.commit()
    return {"status": "ok"}


@router.patch("/users/{user_id}/location")
async def update_user_location(
    user_id: str,
    payload: AdminUserLocationUpdate,
    request: Request,
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
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
            ip_address=client_ip(request),
            user_agent=user_agent(request),
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

    # Verify confirmation matches DELETE or DELETE <email>
    conf = payload.confirmation.strip()
    if conf != "DELETE" and conf != f"DELETE {user.email}":
        raise HTTPException(status_code=400, detail=f'Type "DELETE" or "DELETE {user.email}" to confirm deletion')

    before = {"status": user.status.value, "token_version": user.token_version}
    user.status = UserStatus.DELETED
    user.token_version += 1
    after = {"status": user.status.value, "token_version": user.token_version}

    now = _utcnow()
    sessions = (await db.execute(
        select(RefreshSession).where(
            RefreshSession.user_id == user.id,
            RefreshSession.revoked_at.is_(None),
        )
    )).scalars().all()
    for s in sessions:
        s.revoked_at = now

    db.add(
        AdminActionLog(
            actor_admin_id=admin.id,
            target_user_id=user.id,
            action="user_deleted",
            reason=payload.reason.strip(),
            before_state=before,
            after_state=after,
            ip_address=client_ip(request),
            user_agent=user_agent(request),
        )
    )
    db.add(
        SecurityAuditEvent(
            user_id=user.id,
            event_type="account_deleted_by_admin",
            description=f"Account disabled/deleted by administrator. Reason: {payload.reason.strip()}",
            ip_address=client_ip(request),
            user_agent=user_agent(request),
        )
    )
    await db.commit()
    return {"status": "deleted"}


# ==============================================================================
# 3. BILLING PLANS CRUD
# ==============================================================================

@router.get("/plans", response_model=list[AdminBillingPlanRow])
async def list_billing_plans(
    _: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> list[AdminBillingPlanRow]:
    rows = (
        await db.execute(
            select(
                BillingPlan,
                func.count(Entitlement.id).label("subscribers_count"),
            )
            .outerjoin(Entitlement, Entitlement.billing_plan_id == BillingPlan.id)
            .group_by(BillingPlan.id)
            .order_by(BillingPlan.created_at.desc())
        )
    ).all()

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
            active_subscribers_count=subscribers_count or 0,
            created_at=plan.created_at,
            updated_at=plan.updated_at,
        )
        for plan, subscribers_count in rows
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
                "price": str(plan.price),
                "currency": plan.currency,
            },
            ip_address=client_ip(request),
            user_agent=user_agent(request),
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
        active_subscribers_count=0,
        created_at=plan.created_at,
        updated_at=plan.updated_at,
    )


@router.patch("/plans/{plan_id}", response_model=AdminBillingPlanRow)
async def update_billing_plan(
    plan_id: str,
    payload: AdminBillingPlanUpdate,
    request: Request,
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> AdminBillingPlanRow:
    try:
        pid = uuid.UUID(plan_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid plan id") from exc

    plan = await db.scalar(select(BillingPlan).where(BillingPlan.id == pid))
    if not plan:
        raise HTTPException(status_code=404, detail="Billing plan not found")

    before = {
        "name": plan.name,
        "price": str(plan.price),
        "currency": plan.currency,
        "is_active": plan.is_active,
        "billing_period": plan.billing_period,
        "access_level": plan.access_level,
    }

    if payload.name is not None:
        plan.name = payload.name.strip()
    if payload.access_level is not None:
        plan.access_level = payload.access_level
    if payload.billing_period is not None:
        plan.billing_period = payload.billing_period
    if payload.price is not None:
        plan.price = payload.price
    if payload.currency is not None:
        plan.currency = payload.currency.upper()
    if payload.description is not None:
        plan.description = payload.description.strip() or None
    if payload.google_play_product_id is not None:
        plan.google_play_product_id = payload.google_play_product_id.strip() or None
    if payload.features is not None:
        plan.features = payload.features
    if payload.is_active is not None:
        plan.is_active = payload.is_active

    after = {
        "name": plan.name,
        "price": str(plan.price),
        "currency": plan.currency,
        "is_active": plan.is_active,
        "billing_period": plan.billing_period,
        "access_level": plan.access_level,
    }

    db.add(
        AdminActionLog(
            actor_admin_id=admin.id,
            target_user_id=None,
            action="billing_plan_updated",
            reason=payload.reason.strip(),
            before_state=before,
            after_state=after,
            ip_address=client_ip(request),
            user_agent=user_agent(request),
        )
    )
    await db.commit()
    await db.refresh(plan)

    subscribers_count = await db.scalar(
        select(func.count(Entitlement.id)).where(Entitlement.billing_plan_id == plan.id)
    ) or 0

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
        active_subscribers_count=subscribers_count,
        created_at=plan.created_at,
        updated_at=plan.updated_at,
    )


@router.delete("/plans/{plan_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_billing_plan(
    plan_id: str,
    request: Request,
    reason: str = Query(default="Deleted unused plan", min_length=3, max_length=300),
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> None:
    try:
        pid = uuid.UUID(plan_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid plan id") from exc

    plan = await db.scalar(select(BillingPlan).where(BillingPlan.id == pid))
    if not plan:
        raise HTTPException(status_code=404, detail="Billing plan not found")

    # Guard: check if any subscribers currently have this plan
    subscribers_count = await db.scalar(
        select(func.count(Entitlement.id)).where(Entitlement.billing_plan_id == plan.id)
    ) or 0
    if subscribers_count > 0:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot delete plan '{plan.name}' because {subscribers_count} user(s) are assigned to it. Deactivate or archive the plan instead.",
        )

    before = {"id": str(plan.id), "code": plan.code, "name": plan.name}
    await db.delete(plan)
    db.add(
        AdminActionLog(
            actor_admin_id=admin.id,
            target_user_id=None,
            action="billing_plan_deleted",
            reason=reason.strip(),
            before_state=before,
            after_state=None,
            ip_address=client_ip(request),
            user_agent=user_agent(request),
        )
    )
    await db.commit()


# ==============================================================================
# 4. PAYMENTS MANAGEMENT APIS (WITH ACCOUNTING INTEGRITY & VOIDING)
# ==============================================================================

@router.get("/payments", response_model=AdminPaginatedPayments)
async def list_payments(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=200),
    user_id: str | None = Query(default=None),
    status: str | None = Query(default=None),
    payment_method: str | None = Query(default=None),
    q: str | None = Query(default=None, max_length=120),
    _: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> AdminPaginatedPayments:
    recorder = User.__table__.alias("recorder")
    user_table = User.__table__.alias("payment_user")
    plan = BillingPlan.__table__.alias("payment_plan")

    base_query = (
        select(
            PaymentRecord,
            user_table.c.email.label("user_email"),
            plan.c.name.label("plan_name"),
            recorder.c.email.label("recorder_email"),
        )
        .join(user_table, user_table.c.id == PaymentRecord.user_id)
        .outerjoin(plan, plan.c.id == PaymentRecord.billing_plan_id)
        .outerjoin(recorder, recorder.c.id == PaymentRecord.recorded_by_admin_id)
    )

    if user_id:
        try:
            uid = uuid.UUID(user_id)
            base_query = base_query.where(PaymentRecord.user_id == uid)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail="Invalid user id") from exc

    if status:
        base_query = base_query.where(PaymentRecord.status == status)

    if payment_method:
        base_query = base_query.where(PaymentRecord.payment_method == payment_method)

    if q:
        term = f"%{q.strip()}%"
        base_query = base_query.where(
            or_(
                user_table.c.email.ilike(term),
                PaymentRecord.reference.ilike(term),
                PaymentRecord.provider.ilike(term),
                PaymentRecord.notes.ilike(term),
            )
        )

    count_stmt = select(func.count(PaymentRecord.id)).select_from(base_query.subquery())
    total = await db.scalar(count_stmt) or 0

    offset = (page - 1) * page_size
    base_query = base_query.order_by(PaymentRecord.received_at.desc()).offset(offset).limit(page_size)

    rows = await db.execute(base_query)
    items = [
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

    total_pages = max(1, math.ceil(total / page_size))

    return AdminPaginatedPayments(
        items=items,
        meta=AdminPaginationMeta(
            page=page,
            page_size=page_size,
            total=total,
            total_pages=total_pages,
        ),
    )


@router.post("/payments", response_model=AdminPaymentRow, status_code=201)
async def record_payment(
    payload: AdminPaymentCreate,
    request: Request,
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> AdminPaymentRow:
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
            },
            ip_address=client_ip(request),
            user_agent=user_agent(request),
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


@router.patch("/payments/{payment_id}", response_model=AdminPaymentRow)
async def update_payment_metadata(
    payment_id: str,
    payload: AdminPaymentUpdate,
    request: Request,
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> AdminPaymentRow:
    try:
        pid = uuid.UUID(payment_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid payment id") from exc

    payment = await db.scalar(select(PaymentRecord).where(PaymentRecord.id == pid))
    if not payment:
        raise HTTPException(status_code=404, detail="Payment record not found")

    user = await db.scalar(select(User).where(User.id == payment.user_id))
    plan = (
        await db.scalar(select(BillingPlan).where(BillingPlan.id == payment.billing_plan_id))
        if payment.billing_plan_id
        else None
    )

    before = {
        "payment_method": payment.payment_method,
        "provider": payment.provider,
        "reference": payment.reference,
        "notes": payment.notes,
    }

    if payload.payment_method is not None:
        payment.payment_method = payload.payment_method.strip()
    if payload.provider is not None:
        payment.provider = payload.provider.strip() or None
    if payload.reference is not None:
        payment.reference = payload.reference.strip() or None
    if payload.notes is not None:
        payment.notes = payload.notes.strip() or None

    after = {
        "payment_method": payment.payment_method,
        "provider": payment.provider,
        "reference": payment.reference,
        "notes": payment.notes,
    }

    db.add(
        AdminActionLog(
            actor_admin_id=admin.id,
            target_user_id=payment.user_id,
            action="payment_metadata_updated",
            reason=payload.reason.strip(),
            before_state=before,
            after_state=after,
            ip_address=client_ip(request),
            user_agent=user_agent(request),
        )
    )
    await db.commit()
    await db.refresh(payment)

    return AdminPaymentRow(
        id=str(payment.id),
        user_id=str(payment.user_id),
        user_email=user.email if user else "",
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


@router.post("/payments/{payment_id}/void", response_model=AdminPaymentRow)
async def void_payment(
    payment_id: str,
    payload: AdminPaymentVoidRequest,
    request: Request,
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> AdminPaymentRow:
    try:
        pid = uuid.UUID(payment_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid payment id") from exc

    payment = await db.scalar(select(PaymentRecord).where(PaymentRecord.id == pid))
    if not payment:
        raise HTTPException(status_code=404, detail="Payment record not found")

    if payment.status == "voided":
        raise HTTPException(status_code=400, detail="Payment is already voided")

    user = await db.scalar(select(User).where(User.id == payment.user_id))
    plan = (
        await db.scalar(select(BillingPlan).where(BillingPlan.id == payment.billing_plan_id))
        if payment.billing_plan_id
        else None
    )

    before = {"status": payment.status, "amount": str(payment.amount)}
    payment.status = "voided"
    after = {"status": payment.status, "amount": str(payment.amount)}

    db.add(
        AdminActionLog(
            actor_admin_id=admin.id,
            target_user_id=payment.user_id,
            action="payment_voided",
            reason=payload.reason.strip(),
            before_state=before,
            after_state=after,
            ip_address=client_ip(request),
            user_agent=user_agent(request),
        )
    )
    db.add(
        SecurityAuditEvent(
            user_id=payment.user_id,
            event_type="payment_voided_by_admin",
            description=f"Payment {payment.id} voided by administrator. Reason: {payload.reason.strip()}",
            ip_address=client_ip(request),
            user_agent=user_agent(request),
        )
    )
    await db.commit()
    await db.refresh(payment)

    return AdminPaymentRow(
        id=str(payment.id),
        user_id=str(payment.user_id),
        user_email=user.email if user else "",
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


# ==============================================================================
# 5. SECURITY & AUDIT LOGS APIS
# ==============================================================================

@router.get("/security-events", response_model=AdminPaginatedSecurityEvents)
async def security_events(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=200),
    event_type: str | None = Query(default=None),
    user_id: str | None = Query(default=None),
    q: str | None = Query(default=None, max_length=120),
    _: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> AdminPaginatedSecurityEvents:
    base_query = (
        select(SecurityAuditEvent, User.email)
        .outerjoin(User, User.id == SecurityAuditEvent.user_id)
    )

    if event_type:
        base_query = base_query.where(SecurityAuditEvent.event_type == event_type)

    if user_id:
        try:
            uid = uuid.UUID(user_id)
            base_query = base_query.where(SecurityAuditEvent.user_id == uid)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail="Invalid user id") from exc

    if q:
        term = f"%{q.strip()}%"
        base_query = base_query.where(
            or_(
                SecurityAuditEvent.description.ilike(term),
                SecurityAuditEvent.ip_address.ilike(term),
                User.email.ilike(term),
            )
        )

    count_stmt = select(func.count(SecurityAuditEvent.id)).select_from(base_query.subquery())
    total = await db.scalar(count_stmt) or 0

    offset = (page - 1) * page_size
    base_query = base_query.order_by(SecurityAuditEvent.created_at.desc()).offset(offset).limit(page_size)

    rows = await db.execute(base_query)
    items = [
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

    total_pages = max(1, math.ceil(total / page_size))

    return AdminPaginatedSecurityEvents(
        items=items,
        meta=AdminPaginationMeta(
            page=page,
            page_size=page_size,
            total=total,
            total_pages=total_pages,
        ),
    )


@router.get("/action-logs", response_model=AdminPaginatedActionLogs)
async def action_logs(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=200),
    action: str | None = Query(default=None),
    actor_id: str | None = Query(default=None),
    target_user_id: str | None = Query(default=None),
    q: str | None = Query(default=None, max_length=120),
    _: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> AdminPaginatedActionLogs:
    actor = User.__table__.alias("actor")
    target = User.__table__.alias("target")

    base_query = (
        select(
            AdminActionLog,
            actor.c.email.label("actor_email"),
            target.c.email.label("target_email"),
        )
        .outerjoin(actor, actor.c.id == AdminActionLog.actor_admin_id)
        .outerjoin(target, target.c.id == AdminActionLog.target_user_id)
    )

    if action:
        base_query = base_query.where(AdminActionLog.action == action)

    if actor_id:
        try:
            aid = uuid.UUID(actor_id)
            base_query = base_query.where(AdminActionLog.actor_admin_id == aid)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail="Invalid actor id") from exc

    if target_user_id:
        try:
            tid = uuid.UUID(target_user_id)
            base_query = base_query.where(AdminActionLog.target_user_id == tid)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail="Invalid target user id") from exc

    if q:
        term = f"%{q.strip()}%"
        base_query = base_query.where(
            or_(
                AdminActionLog.reason.ilike(term),
                actor.c.email.ilike(term),
                target.c.email.ilike(term),
            )
        )

    count_stmt = select(func.count(AdminActionLog.id)).select_from(base_query.subquery())
    total = await db.scalar(count_stmt) or 0

    offset = (page - 1) * page_size
    base_query = base_query.order_by(AdminActionLog.created_at.desc()).offset(offset).limit(page_size)

    rows = await db.execute(base_query)
    items = [
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

    total_pages = max(1, math.ceil(total / page_size))

    return AdminPaginatedActionLogs(
        items=items,
        meta=AdminPaginationMeta(
            page=page,
            page_size=page_size,
            total=total,
            total_pages=total_pages,
        ),
    )


# ==============================================================================
# 6. CSV DATA EXPORT APIS
# ==============================================================================

@router.get("/export/{resource}")
async def export_csv(
    resource: str,
    _: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> Response:
    output = io.StringIO()
    writer = csv.writer(output)

    if resource == "users":
        writer.writerow(["ID", "Email", "Full Name", "Status", "Is Admin", "Email Verified", "Plan", "Entitlement Status", "Created At"])
        users = (await db.execute(select(User, Entitlement).outerjoin(Entitlement, Entitlement.user_id == User.id).order_by(User.created_at.desc()))).all()
        for u, ent in users:
            writer.writerow([
                str(u.id),
                u.email,
                u.full_name or "",
                u.status.value,
                u.is_admin,
                u.email_verified,
                ent.plan_code.value if ent else "free",
                ent.status.value if ent else "none",
                u.created_at.isoformat(),
            ])
    elif resource == "payments":
        writer.writerow(["ID", "User ID", "Amount", "Currency", "Method", "Status", "Reference", "Received At"])
        payments = (await db.execute(select(PaymentRecord).order_by(PaymentRecord.received_at.desc()))).scalars().all()
        for p in payments:
            writer.writerow([
                str(p.id),
                str(p.user_id),
                str(p.amount),
                p.currency,
                p.payment_method,
                p.status,
                p.reference or "",
                p.received_at.isoformat(),
            ])
    elif resource == "action_logs":
        writer.writerow(["ID", "Actor ID", "Target User ID", "Action", "Reason", "IP", "Timestamp"])
        logs = (await db.execute(select(AdminActionLog).order_by(AdminActionLog.created_at.desc()).limit(1000))).scalars().all()
        for l in logs:
            writer.writerow([
                str(l.id),
                str(l.actor_admin_id or ""),
                str(l.target_user_id or ""),
                l.action,
                l.reason,
                l.ip_address or "",
                l.created_at.isoformat(),
            ])
    else:
        raise HTTPException(status_code=400, detail="Unsupported export resource")

    filename = f"finpilot_{resource}_{date.today().isoformat()}.csv"
    return Response(
        content=output.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


# ==============================================================================
# 7. EMAIL TEST
# ==============================================================================

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
            ip_address=client_ip(request),
            user_agent=user_agent(request),
        )
    )
    await db.commit()
    return {"status": "sent", "recipient": admin.email}
