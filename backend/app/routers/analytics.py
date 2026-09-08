from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.dependencies.auth import get_current_user
from app.dependencies.entitlements import require_pro_user
from app.models.user import User
from app.schemas.analytics import AnalyticsOverview, AnalyticsReport
from app.services.analytics import build_analytics, build_report

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/overview", response_model=AnalyticsOverview)
async def analytics_overview(
    user: User = Depends(require_pro_user),
    db: AsyncSession = Depends(get_db),
) -> AnalyticsOverview:
    data = await build_analytics(db, user.id)
    return AnalyticsOverview.model_validate(data)



@router.get("/report", response_model=AnalyticsReport)
async def analytics_report(
    months: int = 6,
    user: User = Depends(require_pro_user),
    db: AsyncSession = Depends(get_db),
) -> AnalyticsReport:
    data = await build_report(db, user.id, months=months)
    return AnalyticsReport.model_validate(data)
