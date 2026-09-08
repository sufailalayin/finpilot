from fastapi import FastAPI

from app.routers.health import router as health_router

app = FastAPI(
    title="FinPilot API",
    version="0.1.0",
    description="Personal Finance AI by Hastron Ventures",
)

app.include_router(health_router, prefix="/api/v1")


@app.get("/")
async def root() -> dict[str, str]:
    return {
        "service": "finpilot-api",
        "brand": "FinPilot by Hastron Ventures",
        "status": "running",
    }
