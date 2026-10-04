from fastapi import APIRouter

from app.ai.router import router as ai_router
from app.analytics.router import router as analytics_router
from app.api.routes.health import router as health_router
from app.datasets.router import router as datasets_router
from app.profiling.router import router as profiling_router
from app.users.router import router as auth_router
from app.visualization.router import router as visualization_router

api_router = APIRouter()

# 1. System health endpoints
api_router.include_router(health_router, prefix="", tags=["system"])

# 2. Authentication & Identity endpoints
api_router.include_router(auth_router, prefix="", tags=["auth"])

# 3. Datasets & Ingestion endpoints
api_router.include_router(datasets_router, prefix="", tags=["datasets"])

# 4. Profiling & Semantics endpoints
api_router.include_router(profiling_router, prefix="", tags=["profiling"])

# 5. Deterministic Analytics Engine endpoints
api_router.include_router(analytics_router, prefix="", tags=["analytics"])

# 6. AI Orchestrator & Conversational Analyst endpoints
api_router.include_router(ai_router, prefix="", tags=["ai"])

# 7. Visualization Intelligence endpoints
api_router.include_router(visualization_router, prefix="", tags=["visualizations"])
