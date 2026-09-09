from datetime import datetime, timezone

from app.models.user import Entitlement, EntitlementStatus, PlanCode


def apply_paid_entitlement(
    entitlement: Entitlement,
    *,
    provider: str,
    provider_subscription_id: str,
    provider_product_id: str,
    paid_until: datetime,
) -> Entitlement:
    if paid_until.tzinfo is None:
        paid_until = paid_until.replace(tzinfo=timezone.utc)

    entitlement.plan_code = PlanCode.PRO
    entitlement.status = EntitlementStatus.ACTIVE
    entitlement.provider = provider
    entitlement.provider_subscription_id = provider_subscription_id
    entitlement.provider_product_id = provider_product_id
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



def apply_manual_plan_change(
    entitlement: Entitlement,
    *,
    plan_code: PlanCode,
    entitlement_status: EntitlementStatus | None = None,
) -> None:
    """Apply an administrator plan change with immediately usable defaults."""
    entitlement.plan_code = plan_code

    if entitlement_status is not None:
        entitlement.status = entitlement_status
        return

    entitlement.status = (
        EntitlementStatus.ACTIVE
        if plan_code == PlanCode.PRO
        else EntitlementStatus.EXPIRED
    )
