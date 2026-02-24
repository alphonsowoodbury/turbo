"""Resilient HTTP client for Turbo API communication.

Provides connection pooling, retry with exponential backoff, circuit breaker
pattern, and structured error handling. All agent tools use this client
instead of creating per-request httpx sessions.
"""

import logging
import os
import time
from typing import Any

import httpx

logger = logging.getLogger("turbo.agent.http")

TURBO_API_URL = os.getenv("TURBO_API_URL", "http://localhost:8001/api/v1")
TURBO_API_KEY = os.getenv("TURBO_API_KEY", "")

# Retry configuration
MAX_RETRIES = 3
RETRY_BASE_DELAY = 1.0  # seconds; doubles each retry
RETRYABLE_STATUS_CODES = {502, 503, 504, 429}

# Circuit breaker configuration
CIRCUIT_FAILURE_THRESHOLD = 5
CIRCUIT_RECOVERY_TIMEOUT = 30.0  # seconds


class TurboAPIError(Exception):
    """Structured error from the Turbo API.

    Includes the endpoint, HTTP status, and response body so tool error
    messages can guide the agent toward a fix.
    """

    def __init__(
        self,
        message: str,
        *,
        endpoint: str = "",
        status_code: int = 0,
        body: str = "",
    ) -> None:
        self.endpoint = endpoint
        self.status_code = status_code
        self.body = body
        super().__init__(message)

    def agent_message(self) -> str:
        """Return an error message formatted for the agent to act on."""
        if self.status_code == 404:
            return f"Error: {self.endpoint} not found (404). Try: Use a list tool to find valid IDs."
        if self.status_code == 422:
            return f"Error: Invalid input for {self.endpoint} (422). Details: {self.body}. Try: Check required fields and value formats."
        if self.status_code == 409:
            return f"Error: Conflict on {self.endpoint} (409). Details: {self.body}. Try: Check current state before retrying."
        if self.status_code >= 500:
            return f"Error: Turbo API server error on {self.endpoint} ({self.status_code}). Try: Wait a moment and retry."
        return f"Error: {self.endpoint} returned {self.status_code}. Details: {self.body}"


class CircuitOpenError(TurboAPIError):
    """Raised when the circuit breaker is open — API calls are short-circuited."""

    def __init__(self, recovery_at: float) -> None:
        remaining = max(0, recovery_at - time.monotonic())
        super().__init__(
            f"Circuit breaker open. API calls paused for {remaining:.0f}s.",
            endpoint="(circuit breaker)",
            status_code=0,
        )


def _build_headers() -> dict[str, str]:
    """Build HTTP headers for Turbo API requests."""
    headers: dict[str, str] = {"Content-Type": "application/json"}
    if TURBO_API_KEY:
        headers["Authorization"] = f"Bearer {TURBO_API_KEY}"
    return headers


def _ensure_trailing_slash(path: str) -> str:
    """Ensure path ends with / to avoid 307 redirects from FastAPI."""
    return path if path.endswith("/") else path + "/"


class TurboHTTPClient:
    """Pooled, resilient HTTP client for the Turbo API.

    Features:
    - Connection pooling (single httpx.AsyncClient reused across calls)
    - Retry with exponential backoff for transient failures
    - Circuit breaker to fail fast when the API is down
    - Structured errors with guidance for the agent
    """

    def __init__(
        self,
        base_url: str = TURBO_API_URL,
        max_retries: int = MAX_RETRIES,
        circuit_threshold: int = CIRCUIT_FAILURE_THRESHOLD,
        circuit_timeout: float = CIRCUIT_RECOVERY_TIMEOUT,
    ) -> None:
        self._base_url = base_url
        self._max_retries = max_retries
        self._circuit_threshold = circuit_threshold
        self._circuit_timeout = circuit_timeout

        self._client: httpx.AsyncClient | None = None
        self._consecutive_failures = 0
        self._circuit_open_until: float | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                base_url=self._base_url,
                headers=_build_headers(),
                follow_redirects=True,
                timeout=httpx.Timeout(connect=5.0, read=30.0, write=10.0, pool=5.0),
            )
        return self._client

    def _check_circuit(self) -> None:
        if self._circuit_open_until is not None:
            if time.monotonic() < self._circuit_open_until:
                raise CircuitOpenError(self._circuit_open_until)
            # Recovery window passed — half-open, allow one attempt
            self._circuit_open_until = None
            self._consecutive_failures = 0
            logger.info("Circuit breaker half-open, allowing probe request")

    def _record_success(self) -> None:
        self._consecutive_failures = 0
        self._circuit_open_until = None

    def _record_failure(self) -> None:
        self._consecutive_failures += 1
        if self._consecutive_failures >= self._circuit_threshold:
            self._circuit_open_until = time.monotonic() + self._circuit_timeout
            logger.warning(
                "Circuit breaker opened after %d consecutive failures. "
                "Will retry in %.0fs.",
                self._consecutive_failures,
                self._circuit_timeout,
            )

    async def _request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        json_data: dict[str, Any] | None = None,
    ) -> Any:
        """Execute an HTTP request with retry and circuit breaker."""
        self._check_circuit()
        url = _ensure_trailing_slash(path)
        last_error: Exception | None = None

        for attempt in range(self._max_retries + 1):
            try:
                client = await self._get_client()
                resp = await client.request(
                    method, url, params=params, json=json_data,
                )
                resp.raise_for_status()
                self._record_success()
                return resp.json()

            except httpx.HTTPStatusError as exc:
                status = exc.response.status_code
                body = exc.response.text[:500]

                if status in RETRYABLE_STATUS_CODES and attempt < self._max_retries:
                    delay = RETRY_BASE_DELAY * (2 ** attempt)
                    logger.warning(
                        "Retryable %d on %s %s (attempt %d/%d, backoff %.1fs)",
                        status, method, path, attempt + 1, self._max_retries + 1, delay,
                    )
                    self._record_failure()
                    import asyncio
                    await asyncio.sleep(delay)
                    last_error = exc
                    continue

                # Non-retryable HTTP error
                self._record_failure()
                raise TurboAPIError(
                    f"{method} {path} failed with {status}",
                    endpoint=f"{method} {path}",
                    status_code=status,
                    body=body,
                ) from exc

            except (httpx.ConnectError, httpx.ConnectTimeout) as exc:
                self._record_failure()
                if attempt < self._max_retries:
                    delay = RETRY_BASE_DELAY * (2 ** attempt)
                    logger.warning(
                        "Connection error on %s %s (attempt %d/%d, backoff %.1fs): %s",
                        method, path, attempt + 1, self._max_retries + 1, delay, exc,
                    )
                    import asyncio
                    await asyncio.sleep(delay)
                    last_error = exc
                    continue
                raise TurboAPIError(
                    f"Cannot connect to Turbo API at {self._base_url}",
                    endpoint=f"{method} {path}",
                    status_code=0,
                    body=str(exc),
                ) from exc

            except httpx.TimeoutException as exc:
                self._record_failure()
                if attempt < self._max_retries:
                    delay = RETRY_BASE_DELAY * (2 ** attempt)
                    logger.warning(
                        "Timeout on %s %s (attempt %d/%d, backoff %.1fs)",
                        method, path, attempt + 1, self._max_retries + 1, delay,
                    )
                    import asyncio
                    await asyncio.sleep(delay)
                    last_error = exc
                    continue
                raise TurboAPIError(
                    f"Timeout on {method} {path} after {self._max_retries + 1} attempts",
                    endpoint=f"{method} {path}",
                    status_code=0,
                    body="Request timed out",
                ) from exc

        # Should not reach here, but handle edge case
        raise TurboAPIError(
            f"Request failed after {self._max_retries + 1} attempts",
            endpoint=f"{method} {path}",
            status_code=0,
            body=str(last_error),
        )

    async def get(
        self, path: str, params: dict[str, Any] | None = None
    ) -> Any:
        return await self._request("GET", path, params=params)

    async def post(self, path: str, data: dict[str, Any]) -> Any:
        return await self._request("POST", path, json_data=data)

    async def patch(self, path: str, data: dict[str, Any]) -> Any:
        return await self._request("PATCH", path, json_data=data)

    async def close(self) -> None:
        if self._client and not self._client.is_closed:
            await self._client.aclose()
            self._client = None


# Module-level singleton — tools import and reuse this.
_default_client: TurboHTTPClient | None = None


def get_http_client() -> TurboHTTPClient:
    """Get or create the module-level HTTP client singleton."""
    global _default_client
    if _default_client is None:
        _default_client = TurboHTTPClient()
    return _default_client


async def close_http_client() -> None:
    """Close the module-level HTTP client. Call during shutdown."""
    global _default_client
    if _default_client is not None:
        await _default_client.close()
        _default_client = None
