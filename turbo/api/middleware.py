"""API security middleware."""

import logging
import os
import secrets
import time
from collections import defaultdict, deque

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger("turbo.api.middleware")

# Paths that don't require authentication
PUBLIC_PATHS = {
    "/",
    "/health",
    "/api/docs",
    "/api/redoc",
    "/openapi.json",
    "/api/v1/openapi.json",
}


class APIKeyMiddleware(BaseHTTPMiddleware):
    """Require API key for all non-public endpoints.

    Set TURBO_API_KEY to enable. When not set (local development),
    all requests are allowed.

    Clients pass the key via:
    - Header: Authorization: Bearer <key>
    - Header: X-API-Key: <key>
    """

    async def dispatch(self, request: Request, call_next):
        required_key = os.getenv("TURBO_API_KEY", "")

        # If no key configured, allow all (local dev)
        if not required_key:
            return await call_next(request)

        # Allow public paths
        path = request.url.path.rstrip("/")
        if path in PUBLIC_PATHS or path == "":
            return await call_next(request)

        # Allow WebSocket upgrades to be handled by their own auth
        if request.headers.get("upgrade", "").lower() == "websocket":
            return await call_next(request)

        # Check Authorization header
        auth_header = request.headers.get("authorization", "")
        api_key_header = request.headers.get("x-api-key", "")

        provided_key = ""
        if auth_header.startswith("Bearer "):
            provided_key = auth_header[7:]
        elif api_key_header:
            provided_key = api_key_header

        if not provided_key or not secrets.compare_digest(provided_key, required_key):
            logger.warning(
                "Unauthorized request to %s from %s",
                request.url.path,
                request.client.host if request.client else "unknown",
            )
            return JSONResponse(
                status_code=401,
                content={"detail": "Invalid or missing API key"},
            )

        return await call_next(request)


# Paths with stricter rate limits (AI, terminal, agents)
_STRICT_PREFIXES = (
    "/api/v1/ai/",
    "/api/v1/terminal/",
    "/api/v1/staff/",
    "/api/v1/agents/",
)

# Default: 120 requests/minute. Strict paths: 30 requests/minute.
_DEFAULT_LIMIT = int(os.getenv("RATE_LIMIT_DEFAULT", "120"))
_STRICT_LIMIT = int(os.getenv("RATE_LIMIT_STRICT", "30"))
_WINDOW_SECONDS = 60


class RateLimitMiddleware(BaseHTTPMiddleware):
    """In-memory sliding window rate limiter by client IP.

    Configurable via environment variables:
    - RATE_LIMIT_DEFAULT: requests per minute for normal endpoints (default: 120)
    - RATE_LIMIT_STRICT: requests per minute for AI/write endpoints (default: 30)
    """

    def __init__(self, app):
        super().__init__(app)
        self._windows: dict[str, deque] = defaultdict(lambda: deque())

    def _get_client_ip(self, request: Request) -> str:
        forwarded = request.headers.get("x-forwarded-for")
        if forwarded:
            return forwarded.split(",")[0].strip()
        return request.client.host if request.client else "unknown"

    def _is_strict_path(self, path: str) -> bool:
        return any(path.startswith(p) for p in _STRICT_PREFIXES)

    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        # Skip rate limiting for health checks and static docs
        if path in PUBLIC_PATHS or path == "":
            return await call_next(request)

        client_ip = self._get_client_ip(request)
        limit = _STRICT_LIMIT if self._is_strict_path(path) else _DEFAULT_LIMIT
        now = time.monotonic()

        # Sliding window: track request timestamps per IP
        window = self._windows[client_ip]

        # Evict expired entries
        cutoff = now - _WINDOW_SECONDS
        while window and window[0] < cutoff:
            window.popleft()

        if len(window) >= limit:
            retry_after = int(window[0] - cutoff) + 1
            logger.warning(
                "Rate limit exceeded for %s on %s (%d/%d)",
                client_ip, path, len(window), limit,
            )
            return JSONResponse(
                status_code=429,
                content={"detail": "Too many requests"},
                headers={"Retry-After": str(retry_after)},
            )

        window.append(now)
        return await call_next(request)


def validate_api_key_for_websocket(token: str) -> bool:
    """Check if a WebSocket token matches the configured API key.

    Returns True if:
    - No TURBO_API_KEY is set (local dev mode), or
    - The provided token matches TURBO_API_KEY
    """
    required_key = os.getenv("TURBO_API_KEY", "")
    if not required_key:
        return True
    if not token:
        return False
    return secrets.compare_digest(token, required_key)
