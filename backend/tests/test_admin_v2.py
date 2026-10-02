from decimal import Decimal
from uuid import uuid4
from datetime import datetime, timezone

from app.schemas.admin import (
    AdminAnalyticsOverview,
    AdminAnalyticsUsers,
    AdminAnalyticsRevenue,
    AdminAnalyticsSubscriptions,
    AdminBillingPlanCreate,
    AdminBillingPlanUpdate,
    AdminDeleteUserRequest,
    AdminPaginatedUsers,
    AdminPaginationMeta,
    AdminPaymentCreate,
    AdminPaymentVoidRequest,
    AdminUserRow,
    RevenuePoint,
    UserGrowthPoint,
)


def test_admin_pagination_meta_and_paginated_users():
    meta = AdminPaginationMeta(page=1, page_size=20, total=45, total_pages=3)
    user_row = AdminUserRow(
        id=str(uuid4()),
        email="test@example.com",
        full_name="Test User",
        user_status="active",
        is_admin=False,
        email_verified=True,
        entitlement_status="active",
        plan_code="pro",
        created_at=datetime.now(timezone.utc),
        trial_ends_at=None,
        paid_until=None,
    )
    paginated = AdminPaginatedUsers(items=[user_row], meta=meta)
    assert len(paginated.items) == 1
    assert paginated.meta.total == 45
    assert paginated.meta.total_pages == 3


def test_admin_analytics_schemas_validation():
    overview = AdminAnalyticsOverview(
        total_users=100,
        active_users=90,
        new_users_today=5,
        new_users_7d=25,
        new_users_30d=70,
        active_trials=15,
        paid_users=40,
        free_users=45,
        expired_users=10,
        suspended_users=2,
        revenue_today=Decimal("1500.00"),
        revenue_this_month=Decimal("45000.00"),
        revenue_this_year=Decimal("250000.00"),
        total_recorded_revenue=Decimal("500000.00"),
        ai_requests_today=30,
        ai_requests_7d=210,
        security_events_24h=8,
        failed_login_attempts=3,
        unverified_emails=4,
        finance_accounts=120,
        transactions=1500,
    )
    assert overview.total_users == 100
    assert overview.revenue_this_month == Decimal("45000.00")

    users_growth = AdminAnalyticsUsers(
        period="7d",
        points=[
            UserGrowthPoint(date="2026-10-01", registrations=3, cumulative=95),
            UserGrowthPoint(date="2026-10-02", registrations=5, cumulative=100),
        ],
        total_registrations=8,
    )
    assert len(users_growth.points) == 2
    assert users_growth.points[-1].cumulative == 100

    revenue_analytics = AdminAnalyticsRevenue(
        period="daily",
        points=[
            RevenuePoint(date="2026-10-01", revenue=Decimal("1200.00"), count=2, voided_amount=Decimal("0.00")),
            RevenuePoint(date="2026-10-02", revenue=Decimal("1500.00"), count=3, voided_amount=Decimal("500.00")),
        ],
        total_revenue=Decimal("2700.00"),
        total_transactions=5,
        voided_revenue=Decimal("500.00"),
    )
    assert revenue_analytics.total_revenue == Decimal("2700.00")
    assert revenue_analytics.voided_revenue == Decimal("500.00")


def test_admin_delete_user_confirmation_validation():
    # Accepts DELETE
    req1 = AdminDeleteUserRequest(reason="User request", confirmation="DELETE")
    assert req1.confirmation == "DELETE"

    # Accepts DELETE user@email.com
    req2 = AdminDeleteUserRequest(reason="User request", confirmation="DELETE test@example.com")
    assert req2.confirmation == "DELETE test@example.com"

    # Rejects invalid confirmation string
    import pytest
    from pydantic import ValidationError
    with pytest.raises(ValidationError):
        AdminDeleteUserRequest(reason="User request", confirmation="delete")

    with pytest.raises(ValidationError):
        AdminDeleteUserRequest(reason="User request", confirmation="CANCEL")


def test_admin_payment_void_and_update_schemas():
    void_req = AdminPaymentVoidRequest(reason="Accidental double billing")
    assert void_req.reason == "Accidental double billing"

    pay_create = AdminPaymentCreate(
        user_id=str(uuid4()),
        amount=Decimal("499.00"),
        currency="INR",
        payment_method="UPI",
        received_at=datetime.now(timezone.utc),
        reason="Manual subscription payment",
    )
    assert pay_create.amount == Decimal("499.00")
    assert pay_create.status == "received"
