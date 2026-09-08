from datetime import datetime, timezone

from app.models.user import Entitlement, EntitlementStatus, PlanCode


def apply_paid_entitlement(
    entitlement: Entitlement,
    *,
    provider: str,
    provider_subscription_id: str,
    paid_until: datetime,
) -> Entitlement:
    if paid_until.tzinfo is None:
        paid_until = paid_until.replace(tzinfo=timezone.utc)

    entitlement.plan_code = PlanCode.PRO
    entitlement.status = EntitlementStatus.ACTIVE
    entitlement.provider = provider
    entitlement.provider_subscription_id = provider_subscription_id
    entitlement.paid_until = paid_until
    return entitlement


def normalize_paid_entitlement(
    entitlement: Entitlement,
    *,
    now: datetime | None = None,
) -> Entitlement:
    now = now or datetime.now(timezone.utc)

    if (
        entitlement.status == EntitlementStatus.ACTIVE
        and entitlement.paid_until is not None
        and entitlement.paid_until <= now
    ):
        entitlement.status = EntitlementStatus.EXPIRED
        entitlement.plan_code = PlanCode.FREE

    return entitlement
