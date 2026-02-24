"""Integration tests for the Turbo Agent module.

Tests the full tool→API→response pipeline with mocked HTTP,
hook chain execution, and subagent tool scoping.
"""

import json
from unittest.mock import AsyncMock, patch

import httpx
import pytest

from turbo.agent.hooks import (
    audit_log_tool_call,
    enforce_project_scope,
    rate_limit_tool_calls,
    turbo_hooks,
)
from turbo.agent.http import TurboHTTPClient
from turbo.agent.subagents import TURBO_SUBAGENTS
from turbo.agent.tools import WRITE_TOOLS


# --- Full Tool Pipeline ---


async def test_tool_pipeline_success(monkeypatch, tmp_path):
    """Test: validate → HTTP → response for a successful tool call."""
    import turbo.agent.hooks as hooks_mod

    # Set up audit log
    audit_path = tmp_path / "audit.jsonl"
    monkeypatch.setattr(hooks_mod, "AUDIT_LOG_PATH", str(audit_path))
    monkeypatch.setattr(hooks_mod, "_audit_logger", None)

    # Mock HTTP to return a project
    mock_client = AsyncMock()
    mock_client.get = AsyncMock(return_value=[
        {"id": "proj-1", "name": "Demo", "status": "active"},
    ])
    monkeypatch.setattr("turbo.agent.tools.get_http_client", lambda: mock_client)

    # Run through the hook chain manually
    input_data = {
        "tool_name": "mcp__turbo__list_projects",
        "tool_input": {},
        "hook_event_name": "PreToolUse",
    }

    # 1. Audit log
    result = await audit_log_tool_call(input_data, "tu-1", None)
    assert not result.get("hookSpecificOutput", {}).get("permissionDecision")

    # 2. Rate limit
    result = await rate_limit_tool_calls(input_data, "tu-1", None)
    assert not result.get("hookSpecificOutput", {}).get("permissionDecision")

    # 3. Tool execution
    from turbo.agent.tools import list_projects
    tool_result = await list_projects.handler({})
    assert "isError" not in tool_result
    content = json.loads(tool_result["content"][0]["text"])
    assert len(content) == 1
    assert content[0]["name"] == "Demo"

    # 4. Verify audit was written
    audit_content = audit_path.read_text().strip()
    assert "tool_call" in audit_content


async def test_tool_pipeline_scope_denied(monkeypatch):
    """Test: scope hook blocks unauthorized access before tool runs."""
    monkeypatch.setenv("TURBO_ALLOWED_PROJECT_IDS", "allowed-proj")

    input_data = {
        "tool_name": "mcp__turbo__get_project",
        "tool_input": {"project_id": "blocked-proj"},
        "hook_event_name": "PreToolUse",
    }

    result = await enforce_project_scope(input_data, "tu-1", None)
    output = result.get("hookSpecificOutput", {})
    assert output.get("permissionDecision") == "deny"
    assert "blocked-proj" in output.get("permissionDecisionReason", "")


async def test_tool_pipeline_rate_limited(monkeypatch):
    """Test: rate limiter blocks after threshold exceeded."""
    import turbo.agent.hooks as hooks_mod
    monkeypatch.setattr(hooks_mod, "MAX_CALLS_PER_MINUTE", 3)

    input_data = {
        "tool_name": "mcp__turbo__integration_test_tool",
        "tool_input": {},
        "hook_event_name": "PreToolUse",
    }

    # Fill up the rate limit
    for i in range(3):
        result = await rate_limit_tool_calls(input_data, f"tu-{i}", None)
        assert not result.get("hookSpecificOutput", {}).get("permissionDecision")

    # 4th call should be denied
    result = await rate_limit_tool_calls(input_data, "tu-blocked", None)
    assert result["hookSpecificOutput"]["permissionDecision"] == "deny"


# --- Subagent Tool Scoping ---


def test_triager_cannot_create_issues():
    """Triager subagent must not have access to any write tools."""
    triager = TURBO_SUBAGENTS["triager"]
    triager_tool_names = {t.split("mcp__turbo__")[-1] for t in triager.tools}
    assert triager_tool_names.isdisjoint(WRITE_TOOLS)


def test_planner_cannot_update_issues():
    """Planner can create but cannot update or delete."""
    planner = TURBO_SUBAGENTS["planner"]
    planner_tool_names = {t.split("mcp__turbo__")[-1] for t in planner.tools}
    assert "update_issue" not in planner_tool_names
    assert "start_issue_work" not in planner_tool_names


def test_worker_cannot_create_decisions():
    """Worker can claim and log work but cannot create new decisions."""
    worker = TURBO_SUBAGENTS["worker"]
    worker_tool_names = {t.split("mcp__turbo__")[-1] for t in worker.tools}
    assert "create_decision" not in worker_tool_names
    assert "create_issue" not in worker_tool_names


def test_reporter_cannot_modify_issues():
    """Reporter can only read and comment — no create/update."""
    reporter = TURBO_SUBAGENTS["reporter"]
    reporter_tool_names = {t.split("mcp__turbo__")[-1] for t in reporter.tools}
    assert "create_issue" not in reporter_tool_names
    assert "update_issue" not in reporter_tool_names
    assert "start_issue_work" not in reporter_tool_names


# --- Hook Chain Order ---


def test_hook_chain_has_correct_order():
    """Verify hooks execute in the right order: audit → rate limit → scope → destructive."""
    hooks = turbo_hooks()
    pre = hooks["PreToolUse"]

    # First: audit (matches all tools)
    assert pre[0].matcher == ".*"
    assert audit_log_tool_call in pre[0].hooks

    # Second: rate limit (matches all tools)
    assert pre[1].matcher == ".*"
    assert rate_limit_tool_calls in pre[1].hooks

    # Third: scope enforcement (Turbo tools only)
    assert pre[2].matcher == "mcp__turbo__.*"
    assert enforce_project_scope in pre[2].hooks

    # Fourth: destructive blocking (Bash only)
    assert pre[3].matcher == "Bash"


# --- Validation + Error Pipeline ---


async def test_validation_error_returns_structured_error(monkeypatch):
    """Validation failure returns isError response, not an exception."""
    mock_client = AsyncMock()
    monkeypatch.setattr("turbo.agent.tools.get_http_client", lambda: mock_client)

    from turbo.agent.tools import create_issue

    # Missing required 'title' field
    result = await create_issue.handler({"project_id": "proj-1"})
    assert result.get("isError") is True
    assert "Invalid input" in result["content"][0]["text"]

    # HTTP client should NOT have been called
    mock_client.post.assert_not_awaited()


async def test_api_error_returns_structured_error(monkeypatch):
    """API failure returns isError response with guidance."""
    from turbo.agent.http import TurboAPIError

    mock_client = AsyncMock()
    mock_client.get = AsyncMock(
        side_effect=TurboAPIError(
            "Not found",
            endpoint="GET /projects/bad-id",
            status_code=404,
            body="",
        )
    )
    monkeypatch.setattr("turbo.agent.tools.get_http_client", lambda: mock_client)

    from turbo.agent.tools import get_project

    result = await get_project.handler({"project_id": "bad-id"})
    assert result.get("isError") is True
    text = result["content"][0]["text"]
    assert "404" in text
    assert "list" in text.lower()  # Should suggest using a list tool


# --- HTTP Client Integration ---


async def test_http_client_handles_json_responses():
    """Verify TurboHTTPClient correctly parses JSON responses."""
    handler = httpx.MockTransport(
        lambda request: httpx.Response(
            200,
            json={"projects": [{"id": "p1", "name": "Test"}]},
        )
    )
    client = TurboHTTPClient.__new__(TurboHTTPClient)
    client._base_url = "http://test"
    client._max_retries = 0
    client._circuit_threshold = 5
    client._circuit_timeout = 30.0
    client._consecutive_failures = 0
    client._circuit_open_until = None
    client._client = httpx.AsyncClient(transport=handler, base_url="http://test")

    result = await client.get("/projects")
    assert result["projects"][0]["name"] == "Test"
    await client.close()
