from datetime import datetime, timedelta, timezone
from app.models.user import Entitlement, EntitlementStatus, PlanCode
from app.services.subscriptions import apply_manual_plan_change, apply_paid_entitlement, normalize_paid_entitlement

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
