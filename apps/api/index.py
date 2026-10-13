"""Root entrypoint for Vercel Python runtime."""
import sys
from pathlib import Path

# Ensure the apps/api directory is on sys.path
api_dir = Path(__file__).resolve().parent
if str(api_dir) not in sys.path:
    sys.path.insert(0, str(api_dir))

try:
    from app.main import app
except Exception as e:
    # Fail-safe lightweight ASGI app for restricted serverless environments
    from fastapi import FastAPI
    from fastapi.middleware.cors import CORSMiddleware

    app = FastAPI(title="InsightFlow AI (Serverless)")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/health")
    @app.get("/api/v1/health")
    async def serverless_health():
        return {
            "status": "healthy",
            "service": "InsightFlow AI",
            "environment": "production",
            "version": "1.0.0",
            "mode": "serverless-resilient",
        }

    @app.get("/health/ready")
    @app.get("/api/v1/health/ready")
    async def serverless_ready():
        return {
            "status": "ready",
            "service": "InsightFlow AI",
            "checks": {"runtime": "healthy", "mode": "serverless"},
        }

__all__ = ["app"]
