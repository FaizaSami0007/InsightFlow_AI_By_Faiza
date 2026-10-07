"""ASGI server entrypoint for Vercel Python runtime."""
import sys
from pathlib import Path

api_dir = Path(__file__).resolve().parent
if str(api_dir) not in sys.path:
    sys.path.insert(0, str(api_dir))

from app.main import app

__all__ = ["app"]
