from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI

from app.api.router import api_router
from app.api.routes.health import router as root_health_router
from app.core.config import settings
from app.core.error_handlers import register_error_handlers
from app.core.logging import logger, setup_logging
from app.core.security import setup_security_middleware


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifecycle management: startup and graceful shutdown."""
    # Setup structured logging
    setup_logging(level=settings.log_level, log_format=settings.log_format)
    logger.info(f"Starting {settings.app_name} API in [{settings.app_env}] environment (port={settings.api_port})")
    yield
    logger.info(f"Shutting down {settings.app_name} API")


def create_application() -> FastAPI:
    """Application factory for InsightFlow AI FastAPI backend."""
    app = FastAPI(
        title=settings.app_name,
        version="1.0.0",
        description="InsightFlow AI — AI-Driven Automated Data Analysis & Context-Aware Dashboard Generation",
        docs_url="/docs" if settings.app_env != "production" else None,
        redoc_url="/redoc" if settings.app_env != "production" else None,
        openapi_url="/openapi.json" if settings.app_env != "production" else None,
        lifespan=lifespan,
    )

    # 1. Security & request tracing middleware
    setup_security_middleware(app)

    # 2. Standardized error handlers
    register_error_handlers(app)

    # 3. Root unversioned health endpoint
    app.include_router(root_health_router, prefix="", tags=["system"])

    # 4. Versioned API routers (/api/v1)
    app.include_router(api_router, prefix=settings.api_prefix)

    return app


app = create_application()


@app.get("/", tags=["system"])
async def root():
    """Root metadata endpoint."""
    return {
        "name": settings.app_name,
        "version": "1.0.0",
        "status": "online",
        "docs": "/docs" if settings.app_env != "production" else "disabled in production",
        "api_v1": f"{settings.api_prefix}/health",
    }
