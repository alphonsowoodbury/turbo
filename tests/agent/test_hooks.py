"""Tests for Turbo agent hooks: scope enforcement, destructive command blocking,
audit logging, rate limiting, and hook assembly.
"""

import json
import time
from unittest.mock import AsyncMock, patch

import pytest

import turbo.agent.hooks as hooks_mod
from turbo.agent.hooks import (
    DESTRUCTIVE_PATTERNS,
    _deny,
    _hash_input,
    _issue_project_cache,
    audit_log_tool_call,
    audit_log_tool_result,
    block_destructive_commands,
    clear_issue_cache,
    enforce_project_scope,
    rate_limit_tool_calls,
    reset_rate_limiter,
    turbo_hooks,
)


# --- Helpers ---

ALLOWED_PID = "a1b2c3d4-0000-1111-2222-333344445555"
OTHER_PID = "ffffffff-0000-0000-0000-000000000000"


def _pre_tool_input(tool_name: str, tool_input: dict | None = None) -> dict:
    """Build a minimal input_data dict for PreToolUse hooks."""
    return {
        "tool_name": tool_name,
        "tool_input": tool_input or {},
        "hook_event_name": "PreToolUse",
    }


def _is_denied(result: dict) -> bool:
    """Check if a hook result is a denial."""
    output = result.get("hookSpecificOutput", {})
    return output.get("permissionDecision") == "deny"


def _is_allowed(result: dict) -> bool:
    return not _is_denied(result)


# ===================================================================
# Scope Enforcement
# ===================================================================


async def test_scope_no_restriction():
    """No TURBO_ALLOWED_PROJECT_IDS env var => all calls pass."""
    inp = _pre_tool_input("mcp__turbo__get_project", {"project_id": "any-id"})
    result = await enforce_project_scope(inp, "tu-1", None)
    assert _is_allowed(result)


async def test_scope_allowed_project(monkeypatch):
    monkeypatch.setenv("TURBO_ALLOWED_PROJECT_IDS", ALLOWED_PID)
    inp = _pre_tool_input("mcp__turbo__get_project", {"project_id": ALLOWED_PID})
    result = await enforce_project_scope(inp, "tu-1", None)
    assert _is_allowed(result)


async def test_scope_blocked_project(monkeypatch):
    monkeypatch.setenv("TURBO_ALLOWED_PROJECT_IDS", ALLOWED_PID)
    inp = _pre_tool_input("mcp__turbo__get_project", {"project_id": OTHER_PID})
    result = await enforce_project_scope(inp, "tu-1", None)
    assert _is_denied(result)
    assert OTHER_PID in result["hookSpecificOutput"]["permissionDecisionReason"]


async def test_scope_cross_project_tool_allowed(monkeypatch):
    """Cross-project read tools (no project_id in args) pass."""
    monkeypatch.setenv("TURBO_ALLOWED_PROJECT_IDS", ALLOWED_PID)
    inp = _pre_tool_input("mcp__turbo__list_projects", {})
    result = await enforce_project_scope(inp, "tu-1", None)
    assert _is_allowed(result)


async def test_scope_cross_project_tool_blocked_explicit_pid(monkeypatch):
    """Cross-project tool with explicit out-of-scope project_id is blocked."""
    monkeypatch.setenv("TURBO_ALLOWED_PROJECT_IDS", ALLOWED_PID)
    inp = _pre_tool_input("mcp__turbo__list_issues", {"project_id": OTHER_PID})
    result = await enforce_project_scope(inp, "tu-1", None)
    assert _is_denied(result)


async def test_scope_issue_tool_resolves_project(monkeypatch):
    """Issue-scoped tool resolves project via API; allowed project passes."""
    monkeypatch.setenv("TURBO_ALLOWED_PROJECT_IDS", ALLOWED_PID)

    mock_client = AsyncMock()
    mock_client.get = AsyncMock(return_value={"project_id": ALLOWED_PID})

    with patch("turbo.agent.http.get_http_client", return_value=mock_client):
        inp = _pre_tool_input("mcp__turbo__get_issue", {"issue_id": "iss-1"})
        result = await enforce_project_scope(inp, "tu-1", None)

    assert _is_allowed(result)
    # Verify it was cached
    assert _issue_project_cache.get("iss-1") == ALLOWED_PID


async def test_scope_issue_tool_blocks_wrong_project(monkeypatch):
    """Issue-scoped tool resolves to wrong project => denied."""
    monkeypatch.setenv("TURBO_ALLOWED_PROJECT_IDS", ALLOWED_PID)

    mock_client = AsyncMock()
    mock_client.get = AsyncMock(return_value={"project_id": OTHER_PID})

    with patch("turbo.agent.http.get_http_client", return_value=mock_client):
        inp = _pre_tool_input("mcp__turbo__update_issue", {"issue_id": "iss-2"})
        result = await enforce_project_scope(inp, "tu-1", None)

    assert _is_denied(result)


async def test_scope_issue_tool_cache_hit(monkeypatch):
    """Pre-populated cache avoids HTTP call."""
    monkeypatch.setenv("TURBO_ALLOWED_PROJECT_IDS", ALLOWED_PID)
    _issue_project_cache["cached-iss"] = ALLOWED_PID

    # If an HTTP call were made, this mock would fail because we don't set it up
    inp = _pre_tool_input("mcp__turbo__get_issue", {"issue_id": "cached-iss"})
    result = await enforce_project_scope(inp, "tu-1", None)
    assert _is_allowed(result)


async def test_scope_issue_tool_api_failure_denies(monkeypatch):
    """If API resolution fails, deny for safety."""
    monkeypatch.setenv("TURBO_ALLOWED_PROJECT_IDS", ALLOWED_PID)

    mock_client = AsyncMock()
    mock_client.get = AsyncMock(side_effect=RuntimeError("connection refused"))

    with patch("turbo.agent.http.get_http_client", return_value=mock_client):
        inp = _pre_tool_input("mcp__turbo__log_work", {"issue_id": "iss-3"})
        result = await enforce_project_scope(inp, "tu-1", None)

    assert _is_denied(result)
    assert "safety" in result["hookSpecificOutput"]["permissionDecisionReason"].lower()


# ===================================================================
# Destructive Command Blocking
# ===================================================================


async def test_blocks_rm_rf():
    inp = _pre_tool_input("Bash", {"command": "rm -rf /"})
    result = await block_destructive_commands(inp, "tu-1", None)
    assert _is_denied(result)


async def test_blocks_git_force_push():
    inp = _pre_tool_input("Bash", {"command": "git push --force origin main"})
    result = await block_destructive_commands(inp, "tu-1", None)
    assert _is_denied(result)


async def test_blocks_drop_table():
    inp = _pre_tool_input("Bash", {"command": "psql -c 'DROP TABLE users'"})
    result = await block_destructive_commands(inp, "tu-1", None)
    assert _is_denied(result)


async def test_allows_safe_command():
    inp = _pre_tool_input("Bash", {"command": "ls -la"})
    result = await block_destructive_commands(inp, "tu-1", None)
    assert _is_allowed(result)


async def test_blocks_case_insensitive():
    inp = _pre_tool_input("Bash", {"command": "RM -RF /tmp/junk"})
    result = await block_destructive_commands(inp, "tu-1", None)
    assert _is_denied(result)


# ===================================================================
# Audit Logging
# ===================================================================


async def test_audit_call_logged(monkeypatch, audit_log_path):
    """Verify a JSON entry is written for a tool call."""
    # Reset the audit logger so it picks up our path
    monkeypatch.setattr(hooks_mod, "AUDIT_LOG_PATH", str(audit_log_path))
    monkeypatch.setattr(hooks_mod, "_audit_logger", None)

    inp = _pre_tool_input("mcp__turbo__list_projects", {"status": "active"})
    await audit_log_tool_call(inp, "tu-42", None)

    content = audit_log_path.read_text().strip()
    entry = json.loads(content)
    assert entry["event"] == "tool_call"
    assert entry["tool"] == "mcp__turbo__list_projects"
    assert entry["tool_use_id"] == "tu-42"
    assert "input_hash" in entry
    assert "timestamp" in entry


async def test_audit_result_logged(monkeypatch, audit_log_path):
    """Verify a result entry with is_error field is written."""
    monkeypatch.setattr(hooks_mod, "AUDIT_LOG_PATH", str(audit_log_path))
    monkeypatch.setattr(hooks_mod, "_audit_logger", None)

    inp = {
        "tool_name": "mcp__turbo__get_project",
        "is_error": True,
        "hook_event_name": "PostToolUse",
    }
    await audit_log_tool_result(inp, "tu-43", None)

    content = audit_log_path.read_text().strip()
    entry = json.loads(content)
    assert entry["event"] == "tool_result"
    assert entry["is_error"] is True


async def test_audit_truncates_long_values(monkeypatch, audit_log_path):
    """Input values >200 chars are truncated in the log."""
    monkeypatch.setattr(hooks_mod, "AUDIT_LOG_PATH", str(audit_log_path))
    monkeypatch.setattr(hooks_mod, "_audit_logger", None)

    long_value = "x" * 300
    inp = _pre_tool_input("mcp__turbo__create_issue", {"description": long_value})
    await audit_log_tool_call(inp, "tu-44", None)

    content = audit_log_path.read_text().strip()
    entry = json.loads(content)
    desc = entry["input_summary"]["description"]
    assert len(desc) < 300
    assert desc.endswith("...")


def test_audit_hash_deterministic():
    """Same input produces the same hash."""
    data = {"project_id": "abc", "title": "Hello"}
    h1 = _hash_input(data)
    h2 = _hash_input(data)
    assert h1 == h2
    assert len(h1) == 16  # truncated hex


def test_audit_hash_different_for_different_input():
    h1 = _hash_input({"a": 1})
    h2 = _hash_input({"a": 2})
    assert h1 != h2


# ===================================================================
# Rate Limiting
# ===================================================================


async def test_under_limit_passes(monkeypatch):
    monkeypatch.setenv("TURBO_AGENT_RATE_LIMIT", "10")
    # Reload the module-level constant
    monkeypatch.setattr(hooks_mod, "MAX_CALLS_PER_MINUTE", 10)

    for i in range(5):
        inp = _pre_tool_input("mcp__turbo__list_projects", {})
        result = await rate_limit_tool_calls(inp, f"tu-{i}", None)
        assert _is_allowed(result)


async def test_over_limit_denies(monkeypatch):
    monkeypatch.setattr(hooks_mod, "MAX_CALLS_PER_MINUTE", 5)

    tool_name = "mcp__turbo__list_projects"
    for i in range(5):
        inp = _pre_tool_input(tool_name, {})
        result = await rate_limit_tool_calls(inp, f"tu-{i}", None)
        assert _is_allowed(result)

    # 6th call should be denied
    inp = _pre_tool_input(tool_name, {})
    result = await rate_limit_tool_calls(inp, "tu-denied", None)
    assert _is_denied(result)
    assert "Rate limit" in result["hookSpecificOutput"]["permissionDecisionReason"]


async def test_different_tools_separate_limits(monkeypatch):
    monkeypatch.setattr(hooks_mod, "MAX_CALLS_PER_MINUTE", 3)

    # Fill up tool_a
    for i in range(3):
        inp = _pre_tool_input("tool_a", {})
        result = await rate_limit_tool_calls(inp, f"a-{i}", None)
        assert _is_allowed(result)

    # tool_a should be denied
    inp = _pre_tool_input("tool_a", {})
    result = await rate_limit_tool_calls(inp, "a-denied", None)
    assert _is_denied(result)

    # tool_b should still pass
    inp = _pre_tool_input("tool_b", {})
    result = await rate_limit_tool_calls(inp, "b-0", None)
    assert _is_allowed(result)


async def test_window_slides(monkeypatch):
    """After 60s, old calls drop out of the sliding window."""
    monkeypatch.setattr(hooks_mod, "MAX_CALLS_PER_MINUTE", 2)

    base_time = time.monotonic()
    call_count = 0

    def mock_monotonic():
        nonlocal call_count
        # First 2 calls at base_time, 3rd call at base_time + 61
        if call_count <= 2:
            return base_time
        return base_time + 61.0

    monkeypatch.setattr(time, "monotonic", mock_monotonic)

    # Fill the window
    for i in range(2):
        call_count = i
        inp = _pre_tool_input("sliding_tool", {})
        result = await rate_limit_tool_calls(inp, f"s-{i}", None)
        assert _is_allowed(result)

    # 3rd call should pass because window has slid
    call_count = 3
    inp = _pre_tool_input("sliding_tool", {})
    result = await rate_limit_tool_calls(inp, "s-3", None)
    assert _is_allowed(result)


# ===================================================================
# Hook Assembly
# ===================================================================


def test_turbo_hooks_structure():
    hooks = turbo_hooks()
    assert "PreToolUse" in hooks
    assert "PostToolUse" in hooks
    assert len(hooks["PreToolUse"]) == 4
    assert len(hooks["PostToolUse"]) == 1


def test_turbo_hooks_pre_tool_matchers():
    hooks = turbo_hooks()
    matchers = hooks["PreToolUse"]
    # Audit and rate limit match everything
    assert matchers[0].matcher == ".*"
    assert matchers[1].matcher == ".*"
    # Scope enforcement matches turbo tools
    assert matchers[2].matcher == "mcp__turbo__.*"
    # Destructive filter matches Bash
    assert matchers[3].matcher == "Bash"


def test_turbo_hooks_post_tool_matcher():
    hooks = turbo_hooks()
    assert hooks["PostToolUse"][0].matcher == ".*"


# ===================================================================
# Deny Helper
# ===================================================================


def test_deny_structure():
    result = _deny("blocked", "PreToolUse")
    assert result["hookSpecificOutput"]["permissionDecision"] == "deny"
    assert result["hookSpecificOutput"]["permissionDecisionReason"] == "blocked"
    assert result["hookSpecificOutput"]["hookEventName"] == "PreToolUse"
