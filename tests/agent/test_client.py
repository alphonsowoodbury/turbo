"""Tests for TurboAgent configuration, prompt building, and execution."""

import os
from typing import Any, AsyncIterator
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from turbo.agent.client import TurboAgent, _wrap_prompt


# --- Default Configuration ---


def test_default_config():
    agent = TurboAgent()
    assert agent.model == "claude-sonnet-4-20250514"
    assert agent.max_turns == 25
    assert agent.max_budget_usd == 2.0
    assert agent.project_id is None


def test_custom_config():
    agent = TurboAgent(
        project_id="proj-1",
        model="claude-opus-4-20250514",
        max_turns=10,
        max_budget_usd=5.0,
    )
    assert agent.project_id == "proj-1"
    assert agent.model == "claude-opus-4-20250514"
    assert agent.max_turns == 10
    assert agent.max_budget_usd == 5.0


def test_project_scope_env_var(monkeypatch):
    """Creating TurboAgent with project_id sets TURBO_ALLOWED_PROJECT_IDS."""
    monkeypatch.delenv("TURBO_ALLOWED_PROJECT_IDS", raising=False)
    _ = TurboAgent(project_id="scope-123")
    assert os.environ.get("TURBO_ALLOWED_PROJECT_IDS") == "scope-123"


def test_no_project_does_not_set_env(monkeypatch):
    monkeypatch.delenv("TURBO_ALLOWED_PROJECT_IDS", raising=False)
    _ = TurboAgent()
    assert os.environ.get("TURBO_ALLOWED_PROJECT_IDS") is None


# --- System Prompt ---


def test_system_prompt_without_project():
    agent = TurboAgent()
    prompt = agent._build_system_prompt()
    assert "Turbo Agent" in prompt
    assert "Scope" not in prompt


def test_system_prompt_with_project():
    agent = TurboAgent(project_id="proj-abc")
    prompt = agent._build_system_prompt()
    assert "proj-abc" in prompt
    assert "Scope" in prompt
    assert "restricted" in prompt.lower() or "scoped" in prompt.lower()


def test_system_prompt_mentions_subagents():
    agent = TurboAgent()
    prompt = agent._build_system_prompt()
    assert "triager" in prompt
    assert "planner" in prompt
    assert "reporter" in prompt
    assert "worker" in prompt


# --- Build Options ---


def test_build_options_defaults():
    agent = TurboAgent()
    opts = agent._build_options()
    assert opts.model == "claude-sonnet-4-20250514"
    assert opts.max_turns == 25
    assert opts.max_budget_usd == 2.0
    assert "turbo" in opts.mcp_servers
    assert opts.permission_mode == "acceptEdits"
    assert "mcp__turbo__*" in opts.allowed_tools
    assert "Task" in opts.allowed_tools


def test_build_options_overrides():
    agent = TurboAgent()
    opts = agent._build_options(model="claude-haiku-3-20250307", max_turns=5)
    assert opts.model == "claude-haiku-3-20250307"
    assert opts.max_turns == 5


def test_build_options_includes_hooks():
    agent = TurboAgent()
    opts = agent._build_options()
    assert "PreToolUse" in opts.hooks
    assert "PostToolUse" in opts.hooks


def test_build_options_includes_agents():
    agent = TurboAgent()
    opts = agent._build_options()
    assert "triager" in opts.agents
    assert "planner" in opts.agents
    assert "reporter" in opts.agents
    assert "worker" in opts.agents


# --- _wrap_prompt ---


async def test_wrap_prompt_yields_user_message():
    events = []
    async for event in _wrap_prompt("Hello agent"):
        events.append(event)

    assert len(events) == 1
    assert events[0]["type"] == "user"
    assert events[0]["message"]["role"] == "user"
    assert events[0]["message"]["content"] == "Hello agent"


# --- run() ---


async def test_run_returns_final_text():
    """Mock the query function to yield AssistantMessage then ResultMessage."""
    agent = TurboAgent()

    # Create mock messages
    mock_text_block = MagicMock()
    mock_text_block.text = "Here is the analysis."

    mock_assistant = MagicMock()
    mock_assistant.__class__.__name__ = "AssistantMessage"
    mock_assistant.content = [mock_text_block]

    mock_result = MagicMock()
    mock_result.__class__.__name__ = "ResultMessage"
    mock_result.result = "Final result text"
    mock_result.total_cost_usd = 0.05
    mock_result.num_turns = 2

    async def mock_query(prompt, options):
        # Need to consume the prompt generator
        async for _ in prompt:
            pass
        yield mock_assistant
        yield mock_result

    with patch("turbo.agent.client.query", side_effect=mock_query):
        # Patch isinstance checks by making our mocks match the types
        with patch("turbo.agent.client.AssistantMessage", type(mock_assistant)):
            with patch("turbo.agent.client.ResultMessage", type(mock_result)):
                result = await agent.run("Analyze the project")

    assert result == "Final result text"


# --- stream() ---


async def test_stream_yields_events():
    """Mock query, collect yielded events, verify types."""
    agent = TurboAgent()

    # Text block
    mock_text_block = MagicMock()
    mock_text_block.text = "Processing..."
    del mock_text_block.name  # Ensure hasattr(block, 'name') is False

    # Tool call block
    mock_tool_block = MagicMock()
    mock_tool_block.name = "mcp__turbo__list_projects"
    mock_tool_block.input = {"status": "active"}
    del mock_tool_block.text  # Ensure hasattr(block, 'text') is False

    mock_assistant = MagicMock()
    mock_assistant.__class__.__name__ = "AssistantMessage"
    mock_assistant.content = [mock_text_block, mock_tool_block]

    mock_result = MagicMock()
    mock_result.__class__.__name__ = "ResultMessage"
    mock_result.result = "Done"
    mock_result.total_cost_usd = 0.05
    mock_result.num_turns = 3
    mock_result.session_id = "sess-1"

    async def mock_query(prompt, options):
        async for _ in prompt:
            pass
        yield mock_assistant
        yield mock_result

    events = []
    with patch("turbo.agent.client.query", side_effect=mock_query):
        with patch("turbo.agent.client.AssistantMessage", type(mock_assistant)):
            with patch("turbo.agent.client.ResultMessage", type(mock_result)):
                async for event in agent.stream("Do stuff"):
                    events.append(event)

    # Should have text event, tool_call event, and result event
    types = [e["type"] for e in events]
    assert "text" in types
    assert "tool_call" in types
    assert "result" in types

    result_event = [e for e in events if e["type"] == "result"][0]
    assert result_event["content"]["text"] == "Done"
    assert result_event["content"]["cost"] == 0.05
    assert result_event["content"]["turns"] == 3


# --- Validation ---


def test_invalid_max_turns_raises():
    with pytest.raises(ValueError, match="max_turns"):
        TurboAgent(max_turns=0)


def test_invalid_max_turns_negative_raises():
    with pytest.raises(ValueError, match="max_turns"):
        TurboAgent(max_turns=-1)


def test_invalid_budget_raises():
    with pytest.raises(ValueError, match="max_budget_usd"):
        TurboAgent(max_budget_usd=0)


def test_invalid_budget_negative_raises():
    with pytest.raises(ValueError, match="max_budget_usd"):
        TurboAgent(max_budget_usd=-1.0)


# --- close() ---


async def test_close_cleans_up():
    agent = TurboAgent()
    with patch("turbo.agent.client.close_http_client", new_callable=AsyncMock) as mock_close:
        await agent.close()
        mock_close.assert_awaited_once()


# --- session() ---


def test_session_returns_turbo_session():
    agent = TurboAgent()
    session = agent.session()
    assert session is not None
    assert session._agent is agent
