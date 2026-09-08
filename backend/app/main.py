from fastapi import FastAPI

from app.routers.auth import router as auth_router
from app.routers.dashboard import router as dashboard_router
from app.routers.finance import router as finance_router
from app.routers.health import router as health_router
from app.routers.planning import router as planning_router

app = FastAPI(
    title="FinPilot API",
    version="0.1.0",
    description="Personal Finance AI by Hastron Ventures",
)

app.include_router(health_router, prefix="/api/v1")
app.include_router(auth_router, prefix="/api/v1")
app.include_router(finance_router, prefix="/api/v1")
app.include_router(dashboard_router, prefix="/api/v1")
app.include_router(planning_router, prefix="/api/v1")


@app.get("/")
async def root() -> dict[str, str]:
    return {
        "service": "finpilot-api",
        "brand": "FinPilot by Hastron Ventures",
        "status": "running",
    }
