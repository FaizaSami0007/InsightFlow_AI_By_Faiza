import time
import uuid
from typing import Callable

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.config import settings
from app.core.logging import logger, request_id_ctx


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add secure HTTP response headers according to OWASP guidelines."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=(), payment=()"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
            "font-src 'self' https://fonts.gstatic.com data:; "
            "img-src 'self' data: blob: https:; "
            "connect-src 'self' http://localhost:* http://127.0.0.1:* ws://localhost:* ws://127.0.0.1:*; "
            "frame-ancestors 'none'; object-src 'none'; base-uri 'self';"
        )
        if settings.app_env == "production":
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        return response


class RequestContextMiddleware(BaseHTTPMiddleware):
    """Attach unique X-Request-ID to every request and log response timing."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        req_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        request.state.request_id = req_id
        token = request_id_ctx.set(req_id)
        start_time = time.perf_counter()

        try:
            response = await call_next(request)
            process_time = (time.perf_counter() - start_time) * 1000
            response.headers["X-Request-ID"] = req_id
            response.headers["X-Process-Time-Ms"] = f"{process_time:.2f}"

            # Only log API paths at debug/info
            if not request.url.path.startswith("/docs") and not request.url.path.startswith("/openapi"):
                logger.info(
                    f"{request.method} {request.url.path} - {response.status_code} ({process_time:.1f}ms)",
                    extra={
                        "extra_data": {
                            "status": response.status_code,
                            "duration_ms": round(process_time, 2),
                        }
                    },
                )
            return response
        finally:
            request_id_ctx.reset(token)


def setup_security_middleware(app: FastAPI) -> None:
    """Configure security headers, request tracing, and CORS."""
    # Request tracing & logging
    app.add_middleware(RequestContextMiddleware)

    # Security headers
    app.add_middleware(SecurityHeadersMiddleware)

    # CORS configuration
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["*"],
        expose_headers=["X-Request-ID", "X-Process-Time-Ms"],
    )
