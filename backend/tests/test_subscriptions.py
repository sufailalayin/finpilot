from datetime import datetime, timedelta, timezone
from app.models.user import Entitlement, EntitlementStatus, PlanCode, User
from app.services.subscriptions import apply_manual_plan_change, apply_paid_entitlement, ensure_user_entitlement, normalize_paid_entitlement

def test_paid_entitlement_activation():
    now = datetime.now(timezone.utc)
    entitlement = Entitlement(plan_code=PlanCode.FREE,status=EntitlementStatus.EXPIRED)
    apply_paid_entitlement(entitlement,provider="google_play",provider_subscription_id="token-123",provider_product_id="finpilot_pro_monthly",paid_until=now + timedelta(days=30))
    assert entitlement.plan_code == PlanCode.PRO
    assert entitlement.status == EntitlementStatus.ACTIVE

def test_paid_entitlement_expires():
    now = datetime.now(timezone.utc)
    entitlement = Entitlement(plan_code=PlanCode.PRO,status=EntitlementStatus.ACTIVE,paid_until=now - timedelta(seconds=1))
    normalize_paid_entitlement(entitlement, now=now)
    assert entitlement.plan_code == PlanCode.FREE
    assert entitlement.status == EntitlementStatus.EXPIRED



def test_manual_admin_upgrade_to_pro_becomes_active():
    entitlement = Entitlement(
        plan_code=PlanCode.FREE,
        status=EntitlementStatus.EXPIRED,
    )
    apply_manual_plan_change(
        entitlement,
        plan_code=PlanCode.PRO,
    )
    assert entitlement.plan_code == PlanCode.PRO
    assert entitlement.status == EntitlementStatus.ACTIVE


def test_manual_admin_downgrade_to_free_takes_effect_immediately():
    entitlement = Entitlement(
        plan_code=PlanCode.PRO,
        status=EntitlementStatus.ACTIVE,
    )
    apply_manual_plan_change(
        entitlement,
        plan_code=PlanCode.FREE,
    )
    assert entitlement.plan_code == PlanCode.FREE
    assert entitlement.status == EntitlementStatus.EXPIRED


def test_manual_admin_can_explicitly_override_status():
    entitlement = Entitlement(
        plan_code=PlanCode.FREE,
        status=EntitlementStatus.EXPIRED,
    )
    apply_manual_plan_change(
        entitlement,
        plan_code=PlanCode.PRO,
        entitlement_status=EntitlementStatus.TRIAL,
    )
    assert entitlement.plan_code == PlanCode.PRO
    assert entitlement.status == EntitlementStatus.TRIAL


def test_manual_admin_upgrade_clears_old_trial_date():
    now = datetime.now(timezone.utc)
    entitlement = Entitlement(
        plan_code=PlanCode.PRO,
        status=EntitlementStatus.TRIAL,
        trial_started_at=now - timedelta(days=6),
        trial_ends_at=now + timedelta(days=1),
    )
    apply_manual_plan_change(
        entitlement,
        plan_code=PlanCode.PRO,
        entitlement_status=EntitlementStatus.ACTIVE,
    )
    assert entitlement.status == EntitlementStatus.ACTIVE
    assert entitlement.plan_code == PlanCode.PRO
    assert entitlement.trial_ends_at is None


def test_manual_non_trial_status_never_keeps_trial_end():
    now = datetime.now(timezone.utc)
    entitlement = Entitlement(
        plan_code=PlanCode.PRO,
        status=EntitlementStatus.TRIAL,
        trial_started_at=now,
        trial_ends_at=now + timedelta(days=7),
    )
    apply_manual_plan_change(
        entitlement,
        plan_code=PlanCode.FREE,
        entitlement_status=EntitlementStatus.EXPIRED,
    )
    assert entitlement.status == EntitlementStatus.EXPIRED
    assert entitlement.plan_code == PlanCode.FREE
    assert entitlement.trial_ends_at is None



def test_missing_admin_entitlement_is_repaired_as_active_pro():
    user = User(
        email="admin@example.com",
        password_hash="hash",
        is_admin=True,
    )

    entitlement = ensure_user_entitlement(user)

    assert user.entitlement is entitlement
    assert entitlement.plan_code == PlanCode.PRO
    assert entitlement.status == EntitlementStatus.ACTIVE


def test_missing_regular_entitlement_is_repaired_as_expired_free():
    user = User(
        email="user@example.com",
        password_hash="hash",
        is_admin=False,
    )

    entitlement = ensure_user_entitlement(user)

    assert user.entitlement is entitlement
    assert entitlement.plan_code == PlanCode.FREE
    assert entitlement.status == EntitlementStatus.EXPIRED


def test_existing_entitlement_is_not_replaced():
    existing = Entitlement(
        plan_code=PlanCode.PRO,
        status=EntitlementStatus.TRIAL,
    )
    user = User(
        email="trial@example.com",
        password_hash="hash",
        is_admin=False,
        entitlement=existing,
    )

    entitlement = ensure_user_entitlement(user)

    assert entitlement is existing
    assert user.entitlement is existing
    assert entitlement.status == EntitlementStatus.TRIAL


def test_manual_admin_reactivation_clears_stale_paid_expiry():
    now = datetime.now(timezone.utc)
    entitlement = Entitlement(
        plan_code=PlanCode.FREE,
        status=EntitlementStatus.EXPIRED,
        paid_until=now - timedelta(days=1),
    )

    apply_manual_plan_change(
        entitlement,
        plan_code=PlanCode.PRO,
        entitlement_status=EntitlementStatus.ACTIVE,
        now=now,
    )
    normalize_paid_entitlement(entitlement, now=now)

    assert entitlement.plan_code == PlanCode.PRO
    assert entitlement.status == EntitlementStatus.ACTIVE
    assert entitlement.paid_until is None


def test_manual_admin_reactivation_preserves_future_paid_expiry():
    now = datetime.now(timezone.utc)
    future_expiry = now + timedelta(days=30)
    entitlement = Entitlement(
        plan_code=PlanCode.FREE,
        status=EntitlementStatus.EXPIRED,
        paid_until=future_expiry,
    )

    apply_manual_plan_change(
        entitlement,
        plan_code=PlanCode.PRO,
        entitlement_status=EntitlementStatus.ACTIVE,
        now=now,
    )

    assert entitlement.plan_code == PlanCode.PRO
    assert entitlement.status == EntitlementStatus.ACTIVE
    assert entitlement.paid_until == future_expiry
