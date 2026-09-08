from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import APIRouter, Depends

from app.db.session import get_db
from app.dependencies.admin import get_current_admin
from app.models.ai import AIUsageEvent
from app.models.user import Entitlement, EntitlementStatus, PlanCode, User
from app.schemas.admin import AdminOverview, AdminUserRow

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/overview", response_model=AdminOverview)
async def overview(
    _: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> AdminOverview:
    total_users = await db.scalar(select(func.count(User.id))) or 0
    active_trials = await db.scalar(
        select(func.count(Entitlement.id)).where(Entitlement.status == EntitlementStatus.TRIAL)
    ) or 0
    paid_users = await db.scalar(
        select(func.count(Entitlement.id)).where(
            Entitlement.plan_code == PlanCode.PRO,
            Entitlement.status == EntitlementStatus.ACTIVE,
        )
    ) or 0
    expired_entitlements = await db.scalar(
        select(func.count(Entitlement.id)).where(Entitlement.status == EntitlementStatus.EXPIRED)
    ) or 0
    ai_requests = await db.scalar(select(func.count(AIUsageEvent.id))) or 0

    return AdminOverview(
        total_users=total_users,
        active_trials=active_trials,
        paid_users=paid_users,
        expired_entitlements=expired_entitlements,
        ai_requests=ai_requests,
    )


@router.get("/users", response_model=list[AdminUserRow])
async def users(
    _: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> list[AdminUserRow]:
    rows = await db.execute(
        select(User, Entitlement)
        .outerjoin(Entitlement, Entitlement.user_id == User.id)
        .order_by(User.created_at.desc())
        .limit(200)
    )

    return [
        AdminUserRow(
            id=str(user.id),
            email=user.email,
            full_name=user.full_name,
            entitlement_status=entitlement.status.value if entitlement else None,
            plan_code=entitlement.plan_code.value if entitlement else None,
            trial_ends_at=entitlement.trial_ends_at if entitlement else None,
            paid_until=entitlement.paid_until if entitlement else None,
            created_at=user.created_at,
        )
        for user, entitlement in rows.all()
    ]
