#!/usr/bin/env python3
"""Minimal test of the Turbo Agent against the live API.

Run from a regular terminal (NOT inside Claude Code):

    cd /Volumes/TURBO/turbo-plan
    export ANTHROPIC_API_KEY=sk-ant-...
    .venv/bin/python test_agent.py
"""

import asyncio
import os
import sys

# Ensure we can import turbo
sys.path.insert(0, "/Volumes/TURBO/turbo-plan")


async def test_tools_directly():
    """Test that our tools can reach the Turbo API."""
    import httpx

    api_url = os.getenv("TURBO_API_URL", "http://localhost:8001/api/v1")
    print(f"Testing Turbo API at {api_url}...")

    async with httpx.AsyncClient(follow_redirects=True) as client:
        resp = await client.get(f"{api_url}/projects/")
        print(f"  GET /projects/ -> {resp.status_code} ({len(resp.json())} projects)")

        resp = await client.get(f"{api_url}/issues/")
        issues = resp.json()
        print(f"  GET /issues/ -> {resp.status_code} ({len(issues)} issues)")
        for issue in issues[:3]:
            print(f"    [{issue['priority']:8}] {issue['issue_key']}: {issue['title']}")

    print("  API is working.\n")


async def test_agent_simple():
    """Run the simplest possible Agent SDK query with Turbo tools."""
    from claude_agent_sdk import query, ClaudeAgentOptions, AssistantMessage, ResultMessage
    from turbo.agent.tools import create_turbo_tools_server

    print("Starting Agent SDK with Turbo tools...")
    print("Task: 'List the projects in Turbo and summarize what you find.'\n")

    tools_server = create_turbo_tools_server()

    options = ClaudeAgentOptions(
        model="claude-haiku-4-5-20251001",  # Cheapest model for testing
        system_prompt="You are a helpful assistant. Use the Turbo tools to answer questions about projects and issues.",
        mcp_servers={"turbo": tools_server},
        allowed_tools=["mcp__turbo__*"],
        max_turns=5,
        max_budget_usd=0.10,
        permission_mode="acceptEdits",
    )

    # Workaround: wrap string prompt as async generator to avoid
    # SDK MCP server transport race condition
    # See: https://github.com/anthropics/claude-agent-sdk-python/issues/386
    async def prompt_gen():
        yield {
            "type": "user",
            "message": {
                "role": "user",
                "content": "List the projects in Turbo and tell me how many issues each has. Be brief.",
            },
        }

    try:
        async for message in query(
            prompt=prompt_gen(),
            options=options,
        ):
            if isinstance(message, AssistantMessage):
                for block in message.content:
                    if hasattr(block, "text"):
                        print(f"[agent] {block.text}")
                    elif hasattr(block, "name"):
                        print(f"  [tool] {block.name}({getattr(block, 'input', {})})")
            elif isinstance(message, ResultMessage):
                print(f"\n--- Done ---")
                print(f"  Cost: ${getattr(message, 'total_cost_usd', 0):.4f}")
                print(f"  Turns: {getattr(message, 'num_turns', '?')}")
    except Exception as e:
        print(f"\nError: {type(e).__name__}: {e}")
        print("\nTroubleshooting:")
        print("  1. Make sure you're NOT running inside Claude Code")
        print("  2. Make sure ANTHROPIC_API_KEY is set")
        print("  3. Make sure 'claude' CLI is in your PATH")
        import shutil
        claude_path = shutil.which("claude")
        print(f"  4. Claude CLI location: {claude_path}")
        raise


async def test_full_triage():
    """Run the full TurboAgent with subagents and hooks."""
    from turbo.agent.client import TurboAgent

    print("\n\nStarting full Turbo Agent (with hooks + subagents)...")
    print("Task: 'Triage all open issues and recommend priority order'\n")

    agent = TurboAgent(
        project_id="2bcf76d8-d4d6-47c0-a43f-e046b5b5e35b",
        model="claude-sonnet-4-20250514",
        max_turns=10,
        max_budget_usd=0.50,
    )

    async for event in agent.stream(
        "Triage all open issues in this project. List them in recommended priority order with brief justifications."
    ):
        if event["type"] == "text":
            print(event["content"])
        elif event["type"] == "tool_call":
            print(f"  [calling] {event['content']['name']}")
        elif event["type"] == "result":
            r = event["content"]
            print(f"\n--- Done (cost: ${r['cost']:.4f}, turns: {r['turns']}) ---")

    # Check audit log
    audit_path = os.path.expanduser("~/.turbo/agent-audit.jsonl")
    if os.path.exists(audit_path):
        with open(audit_path) as f:
            lines = f.readlines()
        print(f"\nAudit log: {len(lines)} entries written to {audit_path}")
        for line in lines[-4:]:
            print(f"  {line.strip()}")


async def main():
    # Step 1: Verify API connectivity
    await test_tools_directly()

    # Step 2: Simple agent test (cheap, fast)
    await test_agent_simple()

    # Step 3: Full agent with all features (optional, costs more)
    response = input("\nRun full triage with subagents and hooks? (y/n): ").strip().lower()
    if response == "y":
        await test_full_triage()


if __name__ == "__main__":
    if os.getenv("CLAUDECODE"):
        print("ERROR: Cannot run inside Claude Code. Open a separate terminal.")
        sys.exit(1)

    if not os.getenv("ANTHROPIC_API_KEY"):
        print("ERROR: ANTHROPIC_API_KEY not set.")
        sys.exit(1)

    asyncio.run(main())
