from datetime import datetime, timedelta, timezone

from app.core.config import get_settings
from app.models.user import Entitlement, EntitlementStatus, PlanCode

settings = get_settings()


def create_trial_entitlement() -> Entitlement:
    now = datetime.now(timezone.utc)
    return Entitlement(
        plan_code=PlanCode.PRO,
        status=EntitlementStatus.TRIAL,
        trial_started_at=now,
        trial_ends_at=now + timedelta(days=settings.trial_days),
    )


def normalize_entitlement(entitlement: Entitlement, now: datetime | None = None) -> Entitlement:
    now = now or datetime.now(timezone.utc)
    if (
        entitlement.status == EntitlementStatus.TRIAL
        and entitlement.trial_ends_at is not None
        and entitlement.trial_ends_at <= now
    ):
        entitlement.status = EntitlementStatus.EXPIRED
        entitlement.plan_code = PlanCode.FREE
    return entitlement
