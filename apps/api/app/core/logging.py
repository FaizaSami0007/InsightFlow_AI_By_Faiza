import contextvars
import json
import logging
import sys
from datetime import datetime, timezone
from typing import Any, Dict, Optional

# Context variable for tracing request IDs across async tasks
request_id_ctx: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar("request_id", default=None)

SENSITIVE_KEYS = {
    "password",
    "secret",
    "token",
    "api_key",
    "authorization",
    "access_key",
    "secret_key",
}


def sanitize_data(data: Any) -> Any:
    """Recursively scrub sensitive keys from log metadata."""
    if isinstance(data, dict):
        return {
            k: ("[REDACTED]" if any(s in k.lower() for s in SENSITIVE_KEYS) else sanitize_data(v))
            for k, v in data.items()
        }
    elif isinstance(data, list):
        return [sanitize_data(item) for item in data]
    return data


class StructuredJsonFormatter(logging.Formatter):
    """Format logs as clean, parseable JSON with metadata and request_id."""

    def __init__(self, service_name: str = "insightflow-api") -> None:
        super().__init__()
        self.service_name = service_name

    def format(self, record: logging.LogRecord) -> str:
        log_payload: Dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "service": self.service_name,
            "module": record.name,
            "message": record.getMessage(),
            "request_id": request_id_ctx.get() or getattr(record, "request_id", None),
        }

        if record.exc_info:
            log_payload["exception"] = self.formatException(record.exc_info)

        if hasattr(record, "extra_data") and isinstance(record.extra_data, dict):
            log_payload["details"] = sanitize_data(record.extra_data)

        return json.dumps(log_payload)


class StructuredTextFormatter(logging.Formatter):
    """Format logs as readable colorized text for development with request context."""

    def format(self, record: logging.LogRecord) -> str:
        req_id = request_id_ctx.get() or getattr(record, "request_id", None)
        req_prefix = f"[{req_id[:8]}] " if req_id else ""
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
        base = f"[{timestamp}] [{record.levelname:<7}] [{record.name}] {req_prefix}{record.getMessage()}"
        if record.exc_info:
            base += f"\n{self.formatException(record.exc_info)}"
        return base


def setup_logging(level: str = "INFO", log_format: str = "text") -> logging.Logger:
    """Configure structured logging for the root and application loggers."""
    root_logger = logging.getLogger()
    root_logger.setLevel(level.upper())

    # Remove existing handlers to avoid duplicates
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    stream_handler = logging.StreamHandler(sys.stdout)
    if log_format.lower() == "json":
        stream_handler.setFormatter(StructuredJsonFormatter())
    else:
        stream_handler.setFormatter(StructuredTextFormatter())

    root_logger.addHandler(stream_handler)

    # Tone down noisy third-party loggers
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.error").setLevel(logging.INFO)

    return logging.getLogger("insightflow")


logger = logging.getLogger("insightflow")
