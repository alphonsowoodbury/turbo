"""Tests for TurboHTTPClient: retry, circuit breaker, error handling."""

import pytest
import httpx

import turbo.agent.http as http_mod
from turbo.agent.http import (
    CircuitOpenError,
    TurboAPIError,
    TurboHTTPClient,
    get_http_client,
    _ensure_trailing_slash,
)


# --- Helpers ---


def _client_with_handler(handler, **kwargs):
    """Create a TurboHTTPClient with a custom mock transport handler."""
    client = TurboHTTPClient(
        base_url="http://test-turbo/api/v1",
        **kwargs,
    )
    client._client = httpx.AsyncClient(
        transport=httpx.MockTransport(handler),
        base_url="http://test-turbo/api/v1",
    )
    return client


def _json_handler(status=200, body=None):
    """Return a handler that always responds with the given status and body."""
    payload = body if body is not None else {"ok": True}

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(status_code=status, json=payload, request=request)

    return handler


# --- Basic CRUD ---


async def test_get_success():
    client = _client_with_handler(_json_handler(200, {"id": "abc"}))
    result = await client.get("/projects")
    assert result == {"id": "abc"}


async def test_post_success():
    client = _client_with_handler(_json_handler(200, {"created": True}))
    result = await client.post("/issues", {"title": "New"})
    assert result == {"created": True}


async def test_patch_success():
    client = _client_with_handler(_json_handler(200, {"updated": True}))
    result = await client.patch("/issues/123", {"status": "closed"})
    assert result == {"updated": True}


# --- Error Handling ---


async def test_404_raises_turbo_api_error():
    client = _client_with_handler(_json_handler(404, {"detail": "not found"}))
    with pytest.raises(TurboAPIError) as exc_info:
        await client.get("/projects/missing")
    assert exc_info.value.status_code == 404


async def test_422_raises_turbo_api_error():
    body = {"detail": [{"msg": "field required", "loc": ["body", "title"]}]}
    client = _client_with_handler(_json_handler(422, body))
    with pytest.raises(TurboAPIError) as exc_info:
        await client.post("/issues", {})
    assert exc_info.value.status_code == 422
    assert "field required" in exc_info.value.body


# --- Retry Behaviour ---


async def test_500_retries_then_fails(monkeypatch):
    """Mock 500 on every attempt. Expect 1 + 3 retries = 4 total requests."""
    monkeypatch.setattr(http_mod, "RETRY_BASE_DELAY", 0)
    counter = {"n": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        counter["n"] += 1
        return httpx.Response(status_code=502, json={"error": "bad"}, request=request)

    client = _client_with_handler(handler)
    with pytest.raises(TurboAPIError):
        await client.get("/projects")
    assert counter["n"] == 4  # 1 initial + 3 retries


async def test_503_retries_then_succeeds(monkeypatch):
    """First 2 return 503, third returns 200."""
    monkeypatch.setattr(http_mod, "RETRY_BASE_DELAY", 0)
    counter = {"n": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        counter["n"] += 1
        if counter["n"] <= 2:
            return httpx.Response(status_code=503, json={}, request=request)
        return httpx.Response(status_code=200, json={"ok": True}, request=request)

    client = _client_with_handler(handler)
    result = await client.get("/projects")
    assert result == {"ok": True}
    assert counter["n"] == 3


async def test_connection_error_retries(monkeypatch):
    """ConnectError triggers retry."""
    monkeypatch.setattr(http_mod, "RETRY_BASE_DELAY", 0)
    counter = {"n": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        counter["n"] += 1
        if counter["n"] <= 2:
            raise httpx.ConnectError("connection refused")
        return httpx.Response(status_code=200, json={"ok": True}, request=request)

    client = _client_with_handler(handler)
    result = await client.get("/health")
    assert result == {"ok": True}
    assert counter["n"] == 3


# --- Circuit Breaker ---


async def test_circuit_breaker_opens(monkeypatch):
    """After 5 consecutive failures the circuit opens."""
    monkeypatch.setattr(http_mod, "RETRY_BASE_DELAY", 0)

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(status_code=404, json={}, request=request)

    client = _client_with_handler(handler, circuit_threshold=5, max_retries=0)

    # Trigger 5 failures to open the circuit
    for _ in range(5):
        with pytest.raises(TurboAPIError):
            await client.get("/projects")

    # 6th call should be short-circuited
    with pytest.raises(CircuitOpenError):
        await client.get("/projects")


async def test_circuit_breaker_recovers(monkeypatch):
    """After recovery timeout, the circuit allows a probe request."""
    monkeypatch.setattr(http_mod, "RETRY_BASE_DELAY", 0)

    call_count = {"n": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        call_count["n"] += 1
        if call_count["n"] <= 5:
            return httpx.Response(status_code=404, json={}, request=request)
        return httpx.Response(status_code=200, json={"recovered": True}, request=request)

    client = _client_with_handler(handler, circuit_threshold=5, max_retries=0, circuit_timeout=0.5)

    # Open the circuit
    for _ in range(5):
        with pytest.raises(TurboAPIError):
            await client.get("/projects")

    # Confirm circuit is open
    with pytest.raises(CircuitOpenError):
        await client.get("/projects")

    # Advance past recovery timeout by manipulating _circuit_open_until
    import time
    client._circuit_open_until = time.monotonic() - 1

    # Probe request should succeed
    result = await client.get("/projects")
    assert result == {"recovered": True}


# --- Path Handling ---


def test_trailing_slash_added():
    assert _ensure_trailing_slash("/projects") == "/projects/"
    assert _ensure_trailing_slash("/projects/") == "/projects/"


async def test_requests_use_trailing_slash():
    """Verify the actual request URL ends with a trailing slash."""
    captured_urls = []

    def handler(request: httpx.Request) -> httpx.Response:
        captured_urls.append(str(request.url))
        return httpx.Response(status_code=200, json={}, request=request)

    client = _client_with_handler(handler)
    await client.get("/projects")
    assert captured_urls[0].endswith("/projects/")


# --- Agent Messages ---


def test_agent_message_404():
    err = TurboAPIError("not found", endpoint="GET /projects/abc", status_code=404, body="")
    msg = err.agent_message()
    assert "not found (404)" in msg
    assert "list tool" in msg.lower() or "Try" in msg


def test_agent_message_422():
    err = TurboAPIError("invalid", endpoint="POST /issues", status_code=422, body="title required")
    msg = err.agent_message()
    assert "422" in msg
    assert "title required" in msg


def test_agent_message_500():
    err = TurboAPIError("server err", endpoint="GET /projects", status_code=500, body="")
    msg = err.agent_message()
    assert "server error" in msg.lower()
    assert "500" in msg


# --- Singleton ---


def test_singleton_client(monkeypatch):
    """get_http_client() returns the same instance on repeated calls."""
    # Reset the module-level singleton first
    monkeypatch.setattr(http_mod, "_default_client", None)
    a = get_http_client()
    b = get_http_client()
    assert a is b
    # Clean up
    monkeypatch.setattr(http_mod, "_default_client", None)


# --- close() ---


async def test_close_client():
    """After close(), the internal client is None."""
    client = _client_with_handler(_json_handler(200, {"ok": True}))
    # Ensure client is open
    await client.get("/projects")
    assert client._client is not None
    await client.close()
    assert client._client is None


async def test_close_already_closed():
    """Calling close() twice does not raise."""
    client = _client_with_handler(_json_handler(200, {"ok": True}))
    await client.close()
    await client.close()  # Should not raise


async def test_close_without_open():
    """Calling close() on a fresh client (never used) does not raise."""
    client = TurboHTTPClient(base_url="http://test-turbo/api/v1")
    await client.close()  # _client is None, should be fine


# --- close_http_client singleton ---


async def test_close_http_client_singleton(monkeypatch):
    """close_http_client() resets the module-level singleton to None."""
    from turbo.agent.http import close_http_client

    monkeypatch.setattr(http_mod, "_default_client", None)
    # Create a client via the singleton
    client = get_http_client()
    assert http_mod._default_client is not None
    await close_http_client()
    assert http_mod._default_client is None


async def test_close_http_client_when_none(monkeypatch):
    """close_http_client() when no client exists does not raise."""
    from turbo.agent.http import close_http_client

    monkeypatch.setattr(http_mod, "_default_client", None)
    await close_http_client()  # Should not raise


# --- Timeout retries ---


async def test_timeout_retries_then_fails(monkeypatch):
    """TimeoutException triggers retry then raises TurboAPIError."""
    monkeypatch.setattr(http_mod, "RETRY_BASE_DELAY", 0)
    counter = {"n": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        counter["n"] += 1
        raise httpx.ReadTimeout("timed out")

    client = _client_with_handler(handler)
    with pytest.raises(TurboAPIError, match="Timeout"):
        await client.get("/slow")
    assert counter["n"] == 4  # 1 initial + 3 retries


# --- Agent message edge cases ---


def test_agent_message_409():
    err = TurboAPIError("conflict", endpoint="POST /issues", status_code=409, body="duplicate")
    msg = err.agent_message()
    assert "409" in msg
    assert "duplicate" in msg


def test_agent_message_unknown_status():
    err = TurboAPIError("unknown", endpoint="GET /foo", status_code=418, body="teapot")
    msg = err.agent_message()
    assert "418" in msg
    assert "teapot" in msg
