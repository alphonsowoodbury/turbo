"""TurboAgent — Main autonomous agent built on the Claude Agent SDK.

This is the primary entry point for running Turbo agents. It configures
the Agent SDK with Turbo's in-process tools, security hooks, and
specialized subagents.

Features:
- One-shot execution (run), streaming (stream), and multi-turn (session) modes
- Cost tracking with budget warnings
- Structured logging of agent lifecycle events
- HTTP client cleanup on shutdown
"""

import logging
import os
from typing import Any, AsyncIterator

from claude_agent_sdk import (
    AssistantMessage,
    ClaudeAgentOptions,
    ClaudeSDKClient,
    ResultMessage,
    SystemMessage,
    query,
)

from turbo.agent.hooks import turbo_hooks
from turbo.agent.http import close_http_client
from turbo.agent.subagents import TURBO_SUBAGENTS
from turbo.agent.tools import create_turbo_tools_server

logger = logging.getLogger("turbo.agent.client")


async def _wrap_prompt(text: str) -> AsyncIterator[dict[str, Any]]:
    """Wrap a string prompt as an async generator.

    Workaround for claude-agent-sdk bug where string prompts cause
    'ProcessTransport is not ready for writing' errors when using
    SDK MCP servers. The async generator path triggers proper MCP
    initialization timing in the SDK's stream_input() flow.

    See: https://github.com/anthropics/claude-agent-sdk-python/issues/386
    """
    yield {"type": "user", "message": {"role": "user", "content": text}}


class TurboAgent:
    """Autonomous project management agent powered by Claude Agent SDK.

    Connects to Turbo's API via in-process SDK tools, enforces project-scoped
    access control via hooks, and delegates specialized tasks to subagents.

    Usage:
        agent = TurboAgent(project_id="abc-123")

        # One-shot task
        result = await agent.run("Triage all open issues and recommend priorities")

        # Multi-turn session
        async with agent.session() as session:
            await session.send("What's the status of the project?")
            await session.send("Create issues for the auth feature")
    """

    def __init__(
        self,
        project_id: str | None = None,
        model: str = "claude-sonnet-4-20250514",
        max_turns: int = 25,
        max_budget_usd: float = 2.0,
    ) -> None:
        if max_turns < 1:
            raise ValueError(f"max_turns must be >= 1, got {max_turns}")
        if max_budget_usd <= 0:
            raise ValueError(f"max_budget_usd must be > 0, got {max_budget_usd}")

        self.project_id = project_id
        self.model = model
        self.max_turns = max_turns
        self.max_budget_usd = max_budget_usd
        self._tools_server = create_turbo_tools_server()

        # Set project scope for hooks
        if project_id:
            os.environ["TURBO_ALLOWED_PROJECT_IDS"] = project_id

        logger.info(
            "TurboAgent initialized (model=%s, project=%s, budget=$%.2f)",
            model, project_id or "all", max_budget_usd,
        )

    def _build_system_prompt(self) -> str:
        parts = [
            "You are Turbo Agent, an autonomous project management assistant.",
            "You manage projects, issues, initiatives, and decisions using the Turbo platform.",
            "",
            "## Your tools",
            "You have access to Turbo tools prefixed with mcp__turbo__.",
            "Use these to read and manage project data.",
            "",
            "## Your subagents",
            "You can delegate specialized tasks:",
            "- **triager**: Analyzes issues and recommends priorities (read-only)",
            "- **planner**: Breaks features into issues and records decisions",
            "- **reporter**: Generates status reports",
            "- **worker**: Manages work sessions (claim issues, log progress)",
            "",
            "## Guidelines",
            "- Always check current state before making changes",
            "- Be concise in responses — bullet points over paragraphs",
            "- When creating issues, include clear acceptance criteria",
            "- Respect the work queue ordering unless told otherwise",
            "- Log decisions and their rationale",
        ]

        if self.project_id:
            parts.extend(
                [
                    "",
                    "## Scope",
                    f"You are scoped to project ID: {self.project_id}",
                    "All operations are restricted to this project.",
                ]
            )

        return "\n".join(parts)

    def _build_options(self, **overrides: Any) -> ClaudeAgentOptions:
        opts: dict[str, Any] = {
            "model": self.model,
            "system_prompt": self._build_system_prompt(),
            "mcp_servers": {"turbo": self._tools_server},
            "allowed_tools": [
                "mcp__turbo__*",  # All Turbo tools
                "Task",  # Subagent delegation
            ],
            "agents": TURBO_SUBAGENTS,
            "hooks": turbo_hooks(),
            "max_turns": self.max_turns,
            "max_budget_usd": self.max_budget_usd,
            "permission_mode": "acceptEdits",
        }
        opts.update(overrides)
        return ClaudeAgentOptions(**opts)

    async def run(self, prompt: str, **kwargs: Any) -> str:
        """Execute a one-shot agent task and return the final result.

        Args:
            prompt: The task for the agent to perform.
            **kwargs: Additional ClaudeAgentOptions overrides.

        Returns:
            The agent's final text response.
        """
        logger.info("Starting one-shot run: %s", prompt[:100])
        options = self._build_options(**kwargs)
        result_text = ""
        total_cost = 0.0

        try:
            async for message in query(prompt=_wrap_prompt(prompt), options=options):
                if isinstance(message, ResultMessage):
                    result_text = getattr(message, "result", "") or ""
                    total_cost = getattr(message, "total_cost_usd", 0) or 0
                    turns = getattr(message, "num_turns", 0)
                    logger.info(
                        "Run complete (cost=$%.4f, turns=%d)", total_cost, turns,
                    )
                elif isinstance(message, AssistantMessage):
                    for block in message.content:
                        if hasattr(block, "text"):
                            result_text = block.text
        finally:
            # Log cost warning if approaching budget
            if total_cost > self.max_budget_usd * 0.8:
                logger.warning(
                    "Cost $%.4f exceeds 80%% of budget $%.2f",
                    total_cost, self.max_budget_usd,
                )

        return result_text

    async def stream(
        self, prompt: str, **kwargs: Any
    ) -> AsyncIterator[dict[str, Any]]:
        """Stream agent execution, yielding structured events.

        Yields dicts with 'type' and 'content' keys:
        - {"type": "text", "content": "..."}
        - {"type": "tool_call", "content": {"name": "...", "input": {...}}}
        - {"type": "result", "content": {"text": "...", "cost": ..., "turns": ...}}
        """
        logger.info("Starting streaming run: %s", prompt[:100])
        options = self._build_options(**kwargs)

        async for message in query(prompt=_wrap_prompt(prompt), options=options):
            if isinstance(message, AssistantMessage):
                for block in message.content:
                    if hasattr(block, "text"):
                        yield {"type": "text", "content": block.text}
                    elif hasattr(block, "name"):
                        yield {
                            "type": "tool_call",
                            "content": {
                                "name": block.name,
                                "input": getattr(block, "input", {}),
                            },
                        }
            elif isinstance(message, ResultMessage):
                cost = getattr(message, "total_cost_usd", 0) or 0
                turns = getattr(message, "num_turns", 0)
                logger.info("Stream complete (cost=$%.4f, turns=%d)", cost, turns)

                if cost > self.max_budget_usd * 0.8:
                    logger.warning(
                        "Cost $%.4f exceeds 80%% of budget $%.2f",
                        cost, self.max_budget_usd,
                    )

                yield {
                    "type": "result",
                    "content": {
                        "text": getattr(message, "result", ""),
                        "cost": cost,
                        "turns": turns,
                        "session_id": getattr(message, "session_id", None),
                    },
                }

    def session(self) -> "_TurboSession":
        """Create a multi-turn session for interactive agent conversations."""
        return _TurboSession(self)

    async def close(self) -> None:
        """Clean up resources (HTTP client, etc.)."""
        await close_http_client()
        logger.info("TurboAgent resources cleaned up")


class _TurboSession:
    """Multi-turn agent session using ClaudeSDKClient.

    Maintains conversation context across multiple exchanges.
    """

    def __init__(self, agent: TurboAgent) -> None:
        self._agent = agent
        self._client: ClaudeSDKClient | None = None

    async def __aenter__(self) -> "_TurboSession":
        options = self._agent._build_options()
        self._client = ClaudeSDKClient(options=options)
        await self._client.__aenter__()
        logger.info("Multi-turn session started")
        return self

    async def __aexit__(self, *args: Any) -> None:
        if self._client:
            await self._client.__aexit__(*args)
            self._client = None
            logger.info("Multi-turn session ended")

    async def send(self, message: str) -> str:
        """Send a message and return the agent's response."""
        if not self._client:
            raise RuntimeError("Session not started. Use 'async with' context manager.")

        logger.info("Session message: %s", message[:100])
        await self._client.query(message)
        result_text = ""

        async for msg in self._client.receive_response():
            if isinstance(msg, AssistantMessage):
                for block in msg.content:
                    if hasattr(block, "text"):
                        result_text = block.text
            elif isinstance(msg, ResultMessage):
                result_text = getattr(msg, "result", result_text) or result_text

        return result_text
