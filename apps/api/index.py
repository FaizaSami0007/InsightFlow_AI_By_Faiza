"""Vercel Python entrypoint for InsightFlow AI FastAPI backend."""

from app.main import app

# Export for ASGI server runtimes
__all__ = ["app"]
