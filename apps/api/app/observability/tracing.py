"""Distributed Tracing & Request Latency Spans."""

import contextvars
import time
import uuid
from typing import Any, Dict, List, Optional

trace_id_ctx: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar("trace_id", default=None)
parent_span_ctx: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar("parent_span", default=None)


class Span:
    """Represents an individual unit of work in a distributed trace."""

    def __init__(
        self,
        name: str,
        trace_id: Optional[str] = None,
        parent_span_id: Optional[str] = None,
        tags: Optional[Dict[str, Any]] = None,
    ) -> None:
        self.name = name
        self.span_id = str(uuid.uuid4())[:16]
        self.trace_id = trace_id or trace_id_ctx.get() or str(uuid.uuid4())
        self.parent_span_id = parent_span_id or parent_span_ctx.get()
        self.start_time: float = time.perf_counter()
        self.end_time: Optional[float] = None
        self.duration_ms: float = 0.0
        self.tags: Dict[str, Any] = tags or {}
        self.status: str = "OK"
        self.error: Optional[str] = None
        self._tokens: List[Any] = []

    def __enter__(self) -> "Span":
        self._tokens.append(trace_id_ctx.set(self.trace_id))
        self._tokens.append(parent_span_ctx.set(self.span_id))
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.finish(exc_val)
        while self._tokens:
            token = self._tokens.pop()
            if hasattr(token, "var"):
                token.var.reset(token)

    def finish(self, exc: Optional[Exception] = None) -> None:
        """Mark span as finished, compute elapsed time, and record error if any."""
        if self.end_time is None:
            self.end_time = time.perf_counter()
            self.duration_ms = round((self.end_time - self.start_time) * 1000, 2)
            if exc:
                self.status = "ERROR"
                self.error = str(exc)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize span to dictionary for reporting."""
        return {
            "name": self.name,
            "span_id": self.span_id,
            "trace_id": self.trace_id,
            "parent_span_id": self.parent_span_id,
            "duration_ms": self.duration_ms,
            "status": self.status,
            "error": self.error,
            "tags": self.tags,
        }


class DistributedTracer:
    """Thread-safe collector of recent trace spans."""

    def __init__(self, max_traces: int = 500) -> None:
        self.max_traces = max_traces
        self._spans: List[Dict[str, Any]] = []

    def record_span(self, span: Span) -> None:
        """Store span record in recent trace buffer."""
        span_dict = span.to_dict()
        self._spans.append(span_dict)
        if len(self._spans) > self.max_traces:
            self._spans.pop(0)

    def get_recent_traces(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Retrieve latest trace span entries."""
        return self._spans[-limit:]


tracer = DistributedTracer()
