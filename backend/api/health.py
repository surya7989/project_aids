from fastapi import APIRouter
from datetime import datetime, timezone

health_router = APIRouter()


@health_router.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "version": "1.0.0",
        "uptime": "running",
    }


@health_router.get("/health/ready")
async def readiness_check():
    return {"status": "ready", "timestamp": datetime.now(timezone.utc).isoformat()}


@health_router.get("/health/live")
async def liveness_check():
    return {"status": "alive", "timestamp": datetime.now(timezone.utc).isoformat()}
