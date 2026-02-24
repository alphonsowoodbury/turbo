"""Tests for Turbo subagent definitions."""

import pytest

from turbo.agent.subagents import TURBO_SUBAGENTS
from turbo.agent.tools import WRITE_TOOLS


# --- Structure ---


def test_all_subagents_present():
    expected = {"triager", "planner", "reporter", "worker"}
    assert set(TURBO_SUBAGENTS.keys()) == expected


def test_subagent_has_required_fields():
    for name, agent_def in TURBO_SUBAGENTS.items():
        assert agent_def.description, f"{name} missing description"
        assert agent_def.prompt, f"{name} missing prompt"
        assert agent_def.tools, f"{name} missing tools"
        assert agent_def.model, f"{name} missing model"


# --- Role-Specific Tool Access ---


def _prefixed_write_tools() -> set[str]:
    """Get write tool names with the mcp__turbo__ prefix."""
    return {f"mcp__turbo__{t}" for t in WRITE_TOOLS}


def test_triager_is_read_only():
    """Triager should not have any write tools."""
    triager_tools = set(TURBO_SUBAGENTS["triager"].tools)
    write_tools = _prefixed_write_tools()
    overlap = triager_tools & write_tools
    assert overlap == set(), f"Triager has write tools: {overlap}"


def test_planner_can_create():
    planner_tools = set(TURBO_SUBAGENTS["planner"].tools)
    assert "mcp__turbo__create_issue" in planner_tools
    assert "mcp__turbo__create_decision" in planner_tools


def test_reporter_can_comment():
    reporter_tools = set(TURBO_SUBAGENTS["reporter"].tools)
    assert "mcp__turbo__add_comment" in reporter_tools


def test_worker_can_claim():
    worker_tools = set(TURBO_SUBAGENTS["worker"].tools)
    assert "mcp__turbo__start_issue_work" in worker_tools
    assert "mcp__turbo__log_work" in worker_tools


# --- Tool Name Validation ---


def test_all_tool_names_valid():
    """Every tool name in each subagent must start with 'mcp__turbo__'."""
    for name, agent_def in TURBO_SUBAGENTS.items():
        for tool_name in agent_def.tools:
            assert tool_name.startswith("mcp__turbo__"), (
                f"Subagent '{name}' has tool '{tool_name}' "
                "that does not start with 'mcp__turbo__'"
            )


# --- Model Assignments ---


def test_reporter_uses_haiku():
    """Reporter is a lighter task, should use haiku."""
    assert TURBO_SUBAGENTS["reporter"].model == "haiku"


def test_triager_uses_sonnet():
    assert TURBO_SUBAGENTS["triager"].model == "sonnet"


def test_planner_uses_sonnet():
    assert TURBO_SUBAGENTS["planner"].model == "sonnet"


def test_worker_uses_sonnet():
    assert TURBO_SUBAGENTS["worker"].model == "sonnet"
