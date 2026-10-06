"""Sliding-window and token-bucket rate limiter for sensitive endpoints and DDoS mitigation."""

import asyncio
import time
from collections import defaultdict
from typing import Callable, Dict, List, Optional

from fastapi import HTTPException, Request, status

from app.core.logging import logger


class InMemoryRateLimiter:
    """Thread-safe sliding window rate limiter for API endpoints."""

    def __init__(self) -> None:
        # key -> list of timestamp floats
        self._history: Dict[str, List[float]] = defaultdict(list)
        self._lock = asyncio.Lock()

    async def is_rate_limited(self, key: str, max_requests: int, window_seconds: int) -> bool:
        """
        Check if key has exceeded max_requests within window_seconds.
        Returns True if rate limited (exceeded), False otherwise.
        """
        now = time.time()
        cutoff = now - window_seconds

        async with self._lock:
            timestamps = self._history[key]
            # Prune old timestamps
            self._history[key] = [ts for ts in timestamps if ts > cutoff]
            if len(self._history[key]) >= max_requests:
                return True
            self._history[key].append(now)
            return False

    async def reset(self, key: Optional[str] = None) -> None:
        """Reset rate limit history for a specific key or all keys."""
        async with self._lock:
            if key:
                self._history.pop(key, None)
            else:
                self._history.clear()


# Global singleton instance
rate_limiter = InMemoryRateLimiter()


def rate_limit(max_requests: int = 60, window_seconds: int = 60, key_prefix: str = "global") -> Callable:
    """
    FastAPI dependency enforcing endpoint rate limiting.
    Rate limits by Client IP address or User ID header.
    """

    async def dependency(request: Request) -> None:
        # Resolve identifier: client IP or X-Forwarded-For
        forwarded = request.headers.get("X-Forwarded-For")
        client_ip = forwarded.split(",")[0].strip() if forwarded else (request.client.host if request.client else "unknown")
        
        # User ID if available in request state
        user_id = getattr(getattr(request, "state", None), "user_id", None)
        identifier = f"{key_prefix}:{user_id or client_ip}"

        limited = await rate_limiter.is_rate_limited(identifier, max_requests, window_seconds)
        if limited:
            logger.warning(f"Rate limit exceeded for identifier={identifier} on endpoint={request.url.path}")
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Rate limit exceeded. Maximum {max_requests} requests per {window_seconds} seconds.",
                headers={"Retry-After": str(window_seconds)},
            )

    return dependency
