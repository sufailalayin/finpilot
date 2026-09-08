from datetime import datetime, timezone

from app.models.user import Entitlement, EntitlementStatus, PlanCode
from app.services.trials import normalize_entitlement


def has_pro_access(entitlement: Entitlement | None) -> bool:
    if entitlement is None:
        return False

    normalize_entitlement(entitlement, now=datetime.now(timezone.utc))

    if entitlement.plan_code != PlanCode.PRO:
        return False

    return entitlement.status in {
        EntitlementStatus.TRIAL,
        EntitlementStatus.ACTIVE,
    }
