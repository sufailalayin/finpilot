from datetime import timedelta
from app.models.user import EntitlementStatus, PlanCode
from app.services.trials import create_trial_entitlement

def test_new_trial_is_pro_and_seven_days():
    entitlement = create_trial_entitlement()
    assert entitlement.plan_code == PlanCode.PRO
    assert entitlement.status == EntitlementStatus.TRIAL
    assert entitlement.trial_ends_at - entitlement.trial_started_at == timedelta(days=7)
