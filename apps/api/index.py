"""Root index entrypoint for Vercel Python runtime."""
import sys
from pathlib import Path

# Ensure the apps/api directory is on sys.path
api_dir = Path(__file__).resolve().parent
if str(api_dir) not in sys.path:
    sys.path.insert(0, str(api_dir))

try:
    from app.main import app
except Exception:
    import traceback

    sys.stderr.write(f"FATAL: Failed to initialize FastAPI application:\n{traceback.format_exc()}\n")
    sys.stderr.flush()
    raise

# Top-level ASGI application bindings for Vercel discovery
application = app
handler = app

__all__ = ["app", "application", "handler"]
