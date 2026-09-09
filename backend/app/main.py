from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.core.production import validate_production_settings
from app.routers.admin import router as admin_router
from app.routers.app_release import router as app_release_router
from app.routers.analytics import router as analytics_router
from app.routers.automation import router as automation_router
from app.routers.assets import router as assets_router
from app.routers.ai import router as ai_router
from app.routers.auth import router as auth_router
from app.routers.dashboard import router as dashboard_router
from app.routers.finance import router as finance_router
from app.routers.health import router as health_router
from app.routers.liabilities import router as liabilities_router
from app.routers.planning import router as planning_router
from app.routers.subscriptions import router as subscriptions_router
from app.routers.security_privacy import router as security_privacy_router

settings = get_settings()
validate_production_settings(settings)

app = FastAPI(
    title="FinPilot API",
    version="0.1.0",
    description="Personal Finance AI by Hastron Ventures",
)

origins = [origin.strip() for origin in settings.cors_origins.split(",") if origin.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router, prefix="/api/v1")
app.include_router(liabilities_router, prefix="/api/v1")
app.include_router(auth_router, prefix="/api/v1")
app.include_router(finance_router, prefix="/api/v1")
app.include_router(dashboard_router, prefix="/api/v1")
app.include_router(planning_router, prefix="/api/v1")
app.include_router(ai_router, prefix="/api/v1")
app.include_router(admin_router, prefix="/api/v1")
app.include_router(app_release_router, prefix="/api/v1")
app.include_router(analytics_router, prefix="/api/v1")
app.include_router(automation_router, prefix="/api/v1")
app.include_router(assets_router, prefix="/api/v1")
app.include_router(subscriptions_router, prefix="/api/v1")
app.include_router(security_privacy_router, prefix="/api/v1")


@app.get("/")
async def root() -> dict[str, str]:
    return {
        "service": "finpilot-api",
        "brand": "FinPilot by Hastron Ventures",
        "status": "running",
    }
