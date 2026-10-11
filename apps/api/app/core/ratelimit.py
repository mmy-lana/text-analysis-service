"""In-memory sliding-window rate limiting middleware.

Authenticated callers presenting an X-API-Key header share a per-key window
(60 requests/minute by default). Anonymous callers are bucketed by a salted
HMAC digest of their client IP (20 requests/hour by default). The optional
Redis bridge can be introduced later by replacing the `WindowStore` backend
without touching the middleware contract.
"""

from __future__ import annotations

import time
from collections import deque
from typing import Deque, Dict, Tuple

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

from app.config import settings
from app.core.security import hash_api_key, hash_client_ip


class SlidingWindow:
    """Timestamp deque implementing a sliding-window counter."""

    __slots__ = ("events", "limit", "window_seconds")

    def __init__(self, limit: int, window_seconds: float) -> None:
        self.limit = limit
        self.window_seconds = window_seconds
        self.events: Deque[float] = deque()

    def _prune(self, now: float) -> None:
        cutoff = now - self.window_seconds
        while self.events and self.events[0] <= cutoff:
            self.events.popleft()

    def check(self, now: float) -> tuple[bool, int, float]:
        """Return (allowed, remaining, seconds_until_reset)."""
        self._prune(now)
        if len(self.events) >= self.limit:
            reset_at = self.events[0] + self.window_seconds
            return False, 0, max(reset_at - now, 0.0)
        self.events.append(now)
        return True, self.limit - len(self.events), self.window_seconds


class WindowStore:
    """Bounded dictionary of sliding windows keyed by (scope, identity)."""

    def __init__(self, max_keys: int = 100_000) -> None:
        self._windows: Dict[Tuple[str, str], SlidingWindow] = {}
        self._max_keys = max_keys

    def window(self, scope: str, identity: str, limit: int, window_seconds: float) -> SlidingWindow:
        key = (scope, identity)
        window = self._windows.get(key)
        if window is None:
            if len(self._windows) >= self._max_keys:
                # Evict the oldest half to bound memory under key floods.
                for stale in list(self._windows.keys())[: self._max_keys // 2]:
                    del self._windows[stale]
            window = SlidingWindow(limit, window_seconds)
            self._windows[key] = window
        return window

    def reset(self) -> None:
        """Drop every tracked window (used by test harnesses between tests)."""
        self._windows.clear()


# Module-level singleton so deployments and test harnesses share one store.
GLOBAL_WINDOW_STORE = WindowStore()


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Attaches sliding-window quotas and X-RateLimit-* response headers."""

    EXEMPT_PATHS: frozenset[str] = frozenset({"/docs", "/redoc", "/openapi.json", "/health"})

    def __init__(self, app, store: WindowStore | None = None) -> None:
        super().__init__(app)
        self._store = store or WindowStore()

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        if request.method == "OPTIONS" or request.url.path in self.EXEMPT_PATHS:
            return await call_next(request)

        raw_key = request.headers.get("X-API-Key")
        if raw_key:
            scope, identity = "key", hash_api_key(raw_key)
            limit = settings.rate_limit_authenticated_per_minute
            window_seconds = 60.0
        else:
            client_ip = request.client.host if request.client else "unknown"
            scope, identity = "anon", hash_client_ip(client_ip)
            limit = settings.rate_limit_anonymous_per_hour
            window_seconds = 3600.0

        window = self._store.window(scope, identity, limit, window_seconds)
        allowed, remaining, reset_in = window.check(time.monotonic())

        headers = {
            "X-RateLimit-Limit": str(limit),
            "X-RateLimit-Remaining": str(remaining),
            "X-RateLimit-Reset": str(int(reset_in)),
        }

        if not allowed:
            retry_after = max(1, int(reset_in))
            return JSONResponse(
                status_code=429,
                content={
                    "type": "about:blank",
                    "title": "Rate Limit Exceeded",
                    "status": 429,
                    "detail": "Too many requests. Retry after the reset window.",
                },
                headers={**headers, "Retry-After": str(retry_after)},
                media_type="application/problem+json",
            )

        response = await call_next(request)
        for name, value in headers.items():
            response.headers.setdefault(name, value)
        return response
