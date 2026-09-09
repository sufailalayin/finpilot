from datetime import datetime, timedelta, timezone
from app.models.user import Entitlement, EntitlementStatus, PlanCode
from app.services.trials import create_trial_entitlement, normalize_entitlement

def test_new_trial_is_pro_and_seven_days():
    entitlement = create_trial_entitlement()
    assert entitlement.plan_code == PlanCode.PRO
    assert entitlement.status == EntitlementStatus.TRIAL
    assert entitlement.trial_ends_at - entitlement.trial_started_at == timedelta(days=7)


def test_admin_past_trial_date_normalizes_to_expired_free():
    now = datetime.now(timezone.utc)
    entitlement = Entitlement(
        plan_code=PlanCode.PRO,
        status=EntitlementStatus.TRIAL,
        trial_started_at=now - timedelta(days=7),
        trial_ends_at=now - timedelta(seconds=1),
    )
    normalize_entitlement(entitlement, now=now)
    assert entitlement.status == EntitlementStatus.EXPIRED
    assert entitlement.plan_code == PlanCode.FREE


def test_future_trial_date_remains_active_trial():
    now = datetime.now(timezone.utc)
    entitlement = Entitlement(
        plan_code=PlanCode.PRO,
        status=EntitlementStatus.TRIAL,
        trial_started_at=now,
        trial_ends_at=now + timedelta(days=3),
    )
    normalize_entitlement(entitlement, now=now)
    assert entitlement.status == EntitlementStatus.TRIAL
    assert entitlement.plan_code == PlanCode.PRO
