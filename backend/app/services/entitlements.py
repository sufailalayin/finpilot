from datetime import datetime, timezone

from app.models.user import Entitlement, EntitlementStatus, PlanCode
from app.services.subscriptions import normalize_paid_entitlement
from app.services.trials import normalize_entitlement


def has_pro_access(entitlement: Entitlement | None) -> bool:
    if entitlement is None:
        return False

    now = datetime.now(timezone.utc)
    normalize_entitlement(entitlement, now=now)
    normalize_paid_entitlement(entitlement, now=now)

    if entitlement.plan_code != PlanCode.PRO:
        return False

    return entitlement.status in {
        EntitlementStatus.TRIAL,
        EntitlementStatus.ACTIVE,
    }
