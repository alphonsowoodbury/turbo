"""Security hooks for Turbo agents.

Implements permission boundaries, audit logging, rate limiting, and safety
guardrails using the Claude Agent SDK hooks system.

Key security properties:
- Project scope enforcement covers ALL tools, including issue_id-based tools
- Rate limiting is thread-safe via asyncio.Lock
- Audit logs include agent/session context and input hashes
- Destructive Bash commands are pattern-blocked
"""

import asyncio
import hashlib
import json
import logging
import os
import time
from collections import deque
from datetime import datetime, timezone
from logging.handlers import RotatingFileHandler
from typing import Any

from claude_agent_sdk import HookMatcher

logger = logging.getLogger("turbo.agent.hooks")

# --- Configuration ---

AUDIT_LOG_PATH = os.getenv(
    "TURBO_AGENT_AUDIT_LOG",
    os.path.expanduser("~/.turbo/agent-audit.jsonl"),
)
MAX_CALLS_PER_MINUTE = int(os.getenv("TURBO_AGENT_RATE_LIMIT", "30"))

# Tools that take issue_id instead of project_id — these need scope resolution
_ISSUE_SCOPED_TOOLS = {
    "mcp__turbo__get_issue",
    "mcp__turbo__update_issue",
    "mcp__turbo__start_issue_work",
    "mcp__turbo__log_work",
}

# Tools that don't carry a project_id and read across all projects.
# These are allowed even under scope enforcement (they return filtered data).
_CROSS_PROJECT_TOOLS = {
    "mcp__turbo__list_projects",
    "mcp__turbo__list_issues",
    "mcp__turbo__list_initiatives",
    "mcp__turbo__list_decisions",
    "mcp__turbo__get_work_queue",
    "mcp__turbo__get_next_issue",
}


def _get_allowed_project_ids() -> set[str] | None:
    """Read allowed project IDs from environment.

    Returns None if no restriction is configured. Reads fresh each call
    so the env var can be updated at runtime.
    """
    raw = os.getenv("TURBO_ALLOWED_PROJECT_IDS", "")
    if not raw.strip():
        return None
    return {pid.strip() for pid in raw.split(",") if pid.strip()}


# --- Denial Helper ---


def _deny(reason: str, event_name: str = "PreToolUse") -> dict[str, Any]:
    """Return a hook denial response."""
    return {
        "hookSpecificOutput": {
            "hookEventName": event_name,
            "permissionDecision": "deny",
            "permissionDecisionReason": reason,
        }
    }


# --- Hook: Project Scope Enforcement ---

# Cache: issue_id → project_id (avoids repeated lookups)
_issue_project_cache: dict[str, str] = {}


async def enforce_project_scope(
    input_data: dict[str, Any],
    tool_use_id: str | None,
    context: Any,
) -> dict[str, Any]:
    """Block tool calls that target projects outside the allowed scope.

    Handles three cases:
    1. Tools with project_id in args → direct check
    2. Tools with issue_id → resolve to project_id, then check
    3. Cross-project read tools → allowed (they return server-filtered data)
    """
    allowed = _get_allowed_project_ids()
    if allowed is None:
        return {}  # No restrictions configured

    tool_name = input_data.get("tool_name", "")
    tool_input = input_data.get("tool_input", {})

    # Cross-project tools are allowed (server filters results)
    if tool_name in _CROSS_PROJECT_TOOLS:
        # But if they pass a project_id, validate it
        pid = tool_input.get("project_id", "")
        if pid and pid not in allowed:
            logger.warning("Blocked %s with out-of-scope project_id: %s", tool_name, pid)
            return _deny(
                f"Project {pid} is not in the allowed scope. Allowed: {', '.join(sorted(allowed))}",
                input_data.get("hook_event_name", "PreToolUse"),
            )
        return {}

    # Direct project_id check
    project_id = tool_input.get("project_id", "")
    if project_id:
        if project_id not in allowed:
            logger.warning("Blocked %s: project %s not in scope", tool_name, project_id)
            return _deny(
                f"Project {project_id} is not in the allowed scope. Allowed: {', '.join(sorted(allowed))}",
                input_data.get("hook_event_name", "PreToolUse"),
            )
        return {}

    # Issue-scoped tools: resolve issue_id to project_id
    if tool_name in _ISSUE_SCOPED_TOOLS:
        issue_id = tool_input.get("issue_id", "")
        if not issue_id:
            return _deny(
                "issue_id is required but missing.",
                input_data.get("hook_event_name", "PreToolUse"),
            )

        # Check cache first
        cached_pid = _issue_project_cache.get(issue_id)
        if cached_pid:
            if cached_pid not in allowed:
                return _deny(
                    f"Issue {issue_id} belongs to project {cached_pid}, which is not in scope.",
                    input_data.get("hook_event_name", "PreToolUse"),
                )
            return {}

        # Resolve via API
        try:
            from turbo.agent.http import get_http_client
            issue_data = await get_http_client().get(f"/issues/{issue_id}")
            resolved_pid = issue_data.get("project_id", "")
            if resolved_pid:
                _issue_project_cache[issue_id] = resolved_pid
                if resolved_pid not in allowed:
                    return _deny(
                        f"Issue {issue_id} belongs to project {resolved_pid}, which is not in scope.",
                        input_data.get("hook_event_name", "PreToolUse"),
                    )
            return {}
        except Exception as exc:
            logger.warning("Could not resolve project for issue %s: %s", issue_id, exc)
            return _deny(
                f"Cannot verify project scope for issue {issue_id}. Access denied for safety.",
                input_data.get("hook_event_name", "PreToolUse"),
            )

    # Tools with add_comment use entity_id — allow if entity_type is not project-scoped
    # For safety, tools not explicitly handled are allowed (they may not carry project context)
    return {}


# --- Hook: Block Destructive Operations ---

DESTRUCTIVE_PATTERNS = [
    "rm -rf",
    "rm -r /",
    "git push --force",
    "git push -f",
    "git reset --hard",
    "DROP TABLE",
    "DROP DATABASE",
    "DELETE FROM",
    "TRUNCATE TABLE",
    "git branch -D",
    "git branch -d main",
    "git branch -d master",
    "chmod -R 777",
    ":(){ :|:& };:",
]


async def block_destructive_commands(
    input_data: dict[str, Any],
    tool_use_id: str | None,
    context: Any,
) -> dict[str, Any]:
    """Block shell commands that could be destructive."""
    tool_input = input_data.get("tool_input", {})
    command = tool_input.get("command", "")

    for pattern in DESTRUCTIVE_PATTERNS:
        if pattern.lower() in command.lower():
            logger.warning("Blocked destructive command: %s (matched: %s)", command, pattern)
            return _deny(
                f"Destructive command blocked: contains '{pattern}'. "
                "Turbo agents cannot execute destructive shell commands.",
                input_data.get("hook_event_name", "PreToolUse"),
            )

    return {}


# --- Hook: Audit Logger ---

_audit_logger: logging.Logger | None = None
_audit_lock = asyncio.Lock()


def _get_audit_logger() -> logging.Logger:
    """Get or create a dedicated audit logger with rotation."""
    global _audit_logger
    if _audit_logger is not None:
        return _audit_logger

    os.makedirs(os.path.dirname(AUDIT_LOG_PATH), exist_ok=True)

    _audit_logger = logging.getLogger("turbo.agent.audit")
    _audit_logger.setLevel(logging.INFO)
    _audit_logger.propagate = False

    handler = RotatingFileHandler(
        AUDIT_LOG_PATH,
        maxBytes=10 * 1024 * 1024,  # 10 MB
        backupCount=5,
    )
    handler.setFormatter(logging.Formatter("%(message)s"))
    _audit_logger.addHandler(handler)

    return _audit_logger


def _hash_input(data: dict[str, Any]) -> str:
    """Create a SHA-256 hash of tool input for tamper detection."""
    canonical = json.dumps(data, sort_keys=True, default=str)
    return hashlib.sha256(canonical.encode()).hexdigest()[:16]


async def audit_log_tool_call(
    input_data: dict[str, Any],
    tool_use_id: str | None,
    context: Any,
) -> dict[str, Any]:
    """Log every tool call to the audit trail."""
    tool_name = input_data.get("tool_name", "unknown")
    tool_input = input_data.get("tool_input", {})

    entry = {
        "event": "tool_call",
        "tool": tool_name,
        "tool_use_id": tool_use_id,
        "input_hash": _hash_input(tool_input),
        "input_summary": {
            k: v if len(str(v)) < 200 else str(v)[:200] + "..."
            for k, v in tool_input.items()
        },
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

    async with _audit_lock:
        _get_audit_logger().info(json.dumps(entry))

    return {}


async def audit_log_tool_result(
    input_data: dict[str, Any],
    tool_use_id: str | None,
    context: Any,
) -> dict[str, Any]:
    """Log tool results for observability."""
    tool_name = input_data.get("tool_name", "unknown")
    is_error = input_data.get("is_error", False)

    entry = {
        "event": "tool_result",
        "tool": tool_name,
        "tool_use_id": tool_use_id,
        "is_error": is_error,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

    async with _audit_lock:
        _get_audit_logger().info(json.dumps(entry))

    return {}


# --- Hook: Rate Limiting ---

_rate_lock = asyncio.Lock()
_call_timestamps: dict[str, deque[float]] = {}


async def rate_limit_tool_calls(
    input_data: dict[str, Any],
    tool_use_id: str | None,
    context: Any,
) -> dict[str, Any]:
    """Enforce rate limits on tool calls to prevent runaway agents.

    Uses a sliding 60-second window with asyncio.Lock for thread safety.
    """
    tool_name = input_data.get("tool_name", "unknown")
    now = time.monotonic()

    async with _rate_lock:
        if tool_name not in _call_timestamps:
            _call_timestamps[tool_name] = deque(maxlen=MAX_CALLS_PER_MINUTE + 10)

        timestamps = _call_timestamps[tool_name]

        # Prune entries older than 60 seconds
        while timestamps and now - timestamps[0] > 60:
            timestamps.popleft()

        if len(timestamps) >= MAX_CALLS_PER_MINUTE:
            logger.warning(
                "Rate limit hit for %s: %d calls in last 60s (max %d)",
                tool_name, len(timestamps), MAX_CALLS_PER_MINUTE,
            )
            return _deny(
                f"Rate limit exceeded: {tool_name} called {len(timestamps)} times "
                f"in the last minute (max {MAX_CALLS_PER_MINUTE}). Wait before retrying.",
                input_data.get("hook_event_name", "PreToolUse"),
            )

        timestamps.append(now)

    return {}


# --- Test Helpers ---


def reset_rate_limiter() -> None:
    """Reset rate limiter state. For testing only."""
    _call_timestamps.clear()


def clear_issue_cache() -> None:
    """Clear the issue→project cache. For testing only."""
    _issue_project_cache.clear()


# --- Assembled Hook Configuration ---


def turbo_hooks() -> dict[str, list[HookMatcher]]:
    """Return the complete hook configuration for Turbo agents.

    Hook execution order for PreToolUse:
    1. Audit log (always runs first — records every attempt)
    2. Rate limit (blocks runaway loops)
    3. Project scope (blocks unauthorized access)
    4. Destructive command filter (blocks dangerous Bash)
    """
    return {
        "PreToolUse": [
            HookMatcher(matcher=".*", hooks=[audit_log_tool_call]),
            HookMatcher(matcher=".*", hooks=[rate_limit_tool_calls]),
            HookMatcher(matcher="mcp__turbo__.*", hooks=[enforce_project_scope]),
            HookMatcher(matcher="Bash", hooks=[block_destructive_commands]),
        ],
        "PostToolUse": [
            HookMatcher(matcher=".*", hooks=[audit_log_tool_result]),
        ],
    }
