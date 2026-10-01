from datetime import datetime, timedelta, timezone

from app.models.user import Entitlement, EntitlementStatus, PlanCode
from app.services.entitlements import has_pro_access


def test_active_trial_has_pro_access():
    now = datetime.now(timezone.utc)
    entitlement = Entitlement(
        plan_code=PlanCode.PRO,
        status=EntitlementStatus.TRIAL,
        trial_started_at=now,
        trial_ends_at=now + timedelta(days=7),
    )

    assert has_pro_access(entitlement) is True


def test_expired_trial_has_no_pro_access():
    now = datetime.now(timezone.utc)
    entitlement = Entitlement(
        plan_code=PlanCode.PRO,
        status=EntitlementStatus.TRIAL,
        trial_started_at=now - timedelta(days=8),
        trial_ends_at=now - timedelta(days=1),
    )

    assert has_pro_access(entitlement) is False


def test_active_paid_entitlement_has_pro_access():
    now = datetime.now(timezone.utc)
    entitlement = Entitlement(
        plan_code=PlanCode.PRO,
        status=EntitlementStatus.ACTIVE,
        paid_until=now + timedelta(days=30),
    )

    assert has_pro_access(entitlement) is True
    assert entitlement.plan_code == PlanCode.PRO
    assert entitlement.status == EntitlementStatus.ACTIVE


def test_expired_paid_entitlement_has_no_pro_access_and_is_normalized():
    now = datetime.now(timezone.utc)
    entitlement = Entitlement(
        plan_code=PlanCode.PRO,
        status=EntitlementStatus.ACTIVE,
        paid_until=now - timedelta(seconds=1),
    )

    assert has_pro_access(entitlement) is False
    assert entitlement.plan_code == PlanCode.FREE
    assert entitlement.status == EntitlementStatus.EXPIRED
