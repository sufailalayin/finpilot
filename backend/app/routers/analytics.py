from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.schemas.analytics import AnalyticsOverview
from app.services.analytics import build_analytics

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/overview", response_model=AnalyticsOverview)
async def analytics_overview(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> AnalyticsOverview:
    data = await build_analytics(db, user.id)
    return AnalyticsOverview.model_validate(data)
