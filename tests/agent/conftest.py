"""Fixtures for Turbo Agent test suite.

Provides mock HTTP transports, sample data, environment isolation,
and hook state cleanup for all agent tests.
"""

import json
import os
from typing import Any
from unittest.mock import AsyncMock

import httpx
import pytest

from turbo.agent.hooks import clear_issue_cache, reset_rate_limiter
from turbo.agent.http import TurboHTTPClient


# --- Mock HTTP Transport ---


def _make_handler(
    status: int = 200,
    body: dict[str, Any] | list[Any] | None = None,
):
    """Create an httpx transport handler returning a canned response."""
    payload = body if body is not None else {"ok": True}

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            status_code=status,
            json=payload,
            request=request,
        )

    return handler


@pytest.fixture
def mock_http_transport():
    """httpx.MockTransport that returns a 200 JSON response by default."""
    return httpx.MockTransport(_make_handler())


@pytest.fixture
def mock_http_client(mock_http_transport):
    """TurboHTTPClient wired to the mock transport (no real network)."""
    client = TurboHTTPClient(base_url="http://test-turbo/api/v1")
    # Pre-create the async client with the mock transport so _get_client()
    # returns our mock instead of a real connection.
    client._client = httpx.AsyncClient(
        transport=mock_http_transport,
        base_url="http://test-turbo/api/v1",
    )
    return client


# --- Sample Data ---


@pytest.fixture
def sample_project_data():
    """Dict with typical project fields."""
    return {
        "id": "a1b2c3d4-0000-1111-2222-333344445555",
        "name": "Turbo Core",
        "description": "Core platform project",
        "status": "active",
        "priority": "high",
        "issue_count": 12,
        "created_at": "2025-12-01T00:00:00Z",
        "updated_at": "2026-02-20T12:00:00Z",
    }


@pytest.fixture
def sample_issue_data(sample_project_data):
    """Dict with typical issue fields."""
    return {
        "id": "f1e2d3c4-aaaa-bbbb-cccc-ddddeeee0001",
        "project_id": sample_project_data["id"],
        "title": "Implement auth middleware",
        "description": "Add JWT-based auth to the API layer",
        "type": "feature",
        "status": "open",
        "priority": "high",
        "issue_key": "TURBO-42",
        "created_at": "2026-01-15T09:00:00Z",
        "updated_at": "2026-02-18T14:30:00Z",
    }


@pytest.fixture
def sample_issues_list(sample_project_data):
    """List of 3 sample issues with different priorities."""
    pid = sample_project_data["id"]
    return [
        {
            "id": "f1e2d3c4-aaaa-bbbb-cccc-ddddeeee0001",
            "project_id": pid,
            "title": "Implement auth middleware",
            "status": "open",
            "priority": "high",
            "issue_key": "TURBO-42",
        },
        {
            "id": "f1e2d3c4-aaaa-bbbb-cccc-ddddeeee0002",
            "project_id": pid,
            "title": "Fix pagination bug",
            "status": "in_progress",
            "priority": "critical",
            "issue_key": "TURBO-43",
        },
        {
            "id": "f1e2d3c4-aaaa-bbbb-cccc-ddddeeee0003",
            "project_id": pid,
            "title": "Update README",
            "status": "open",
            "priority": "low",
            "issue_key": "TURBO-44",
        },
    ]


# --- Audit Log Path ---


@pytest.fixture
def audit_log_path(tmp_path):
    """Temporary audit log file path for testing."""
    return tmp_path / "test-audit.jsonl"


# --- Environment Isolation ---


@pytest.fixture(autouse=True)
def clean_env(monkeypatch):
    """Save and restore agent-specific env vars so tests don't leak state."""
    # Remove agent-specific vars to ensure a clean slate
    for var in ("TURBO_ALLOWED_PROJECT_IDS", "TURBO_AGENT_RATE_LIMIT"):
        monkeypatch.delenv(var, raising=False)
    yield


# --- Hook State Cleanup ---


@pytest.fixture(autouse=True)
def reset_hooks():
    """Reset rate limiter counters and issue cache between tests."""
    reset_rate_limiter()
    clear_issue_cache()
    yield
    reset_rate_limiter()
    clear_issue_cache()
