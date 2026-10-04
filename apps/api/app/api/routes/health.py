from datetime import datetime, timezone
from typing import Any, Dict

from fastapi import APIRouter, status
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.database.session import check_database_health

router = APIRouter(tags=["system"])


@router.get("/health", summary="Basic service liveness check")
async def liveness() -> Dict[str, Any]:
    """Lightweight liveness probe returning service metadata and UTC timestamp."""
    return {
        "status": "healthy",
        "service": settings.app_name,
        "environment": settings.app_env,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "version": "1.0.0",
    }


@router.get("/health/ready", summary="Service readiness probe")
async def readiness() -> JSONResponse:
    """Readiness probe verifying essential dependency connectivity (e.g. database)."""
    db_ok = await check_database_health()
    overall_status = "ready" if db_ok else "degraded"
    status_code = status.HTTP_200_OK if db_ok else status.HTTP_503_SERVICE_UNAVAILABLE

    payload = {
        "status": overall_status,
        "service": settings.app_name,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "checks": {
            "database": "reachable" if db_ok else "unreachable",
        },
    }
    return JSONResponse(status_code=status_code, content=payload)
