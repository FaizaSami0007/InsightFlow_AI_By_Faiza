from fastapi import APIRouter

from app.api.routes.health import router as health_router
from app.datasets.router import router as datasets_router
from app.users.router import router as auth_router

api_router = APIRouter()

# 1. System health endpoints
api_router.include_router(health_router, prefix="", tags=["system"])

# 2. Authentication & Identity endpoints
api_router.include_router(auth_router, prefix="", tags=["auth"])

# 3. Datasets & Ingestion endpoints
api_router.include_router(datasets_router, prefix="", tags=["datasets"])
