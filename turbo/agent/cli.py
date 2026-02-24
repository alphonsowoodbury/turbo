#!/usr/bin/env python3
"""CLI entry point for running Turbo agents.

Usage:
    # One-shot task
    turbo-agent "Triage all open issues in the project"

    # With project scope
    turbo-agent --project abc-123 "Generate a status report"

    # Interactive session
    turbo-agent --interactive

    # Stream output with verbose tool calls
    turbo-agent --stream --verbose "Break down the auth feature into issues"

    # Save output to file
    turbo-agent --output report.md "Generate a status report"
"""

import argparse
import asyncio
import sys

from turbo.agent.client import TurboAgent
from turbo.agent.logging import configure_agent_logging


async def run_oneshot(
    agent: TurboAgent,
    prompt: str,
    stream: bool = False,
    verbose: bool = False,
    output_path: str | None = None,
) -> None:
    """Run a single agent task."""
    result_text = ""

    if stream:
        async for event in agent.stream(prompt):
            if event["type"] == "text":
                print(event["content"])
                result_text = event["content"]
            elif event["type"] == "tool_call" and verbose:
                tool = event["content"]
                print(f"  [tool] {tool['name']}", file=sys.stderr)
            elif event["type"] == "result":
                result = event["content"]
                print(
                    f"\n--- Done (cost: ${result['cost']:.4f}, turns: {result['turns']}) ---",
                    file=sys.stderr,
                )
    else:
        result_text = await agent.run(prompt)
        print(result_text)

    if output_path and result_text:
        with open(output_path, "w") as f:
            f.write(result_text)
        print(f"\nOutput saved to {output_path}", file=sys.stderr)


async def run_interactive(agent: TurboAgent) -> None:
    """Run an interactive multi-turn agent session."""
    print("Turbo Agent (interactive mode)")
    print("Type 'quit' or 'exit' to end the session.\n")

    async with agent.session() as session:
        while True:
            try:
                user_input = input("you> ").strip()
            except (EOFError, KeyboardInterrupt):
                print("\nExiting.")
                break

            if user_input.lower() in ("quit", "exit", "q"):
                break
            if not user_input:
                continue

            response = await session.send(user_input)
            print(f"\nagent> {response}\n")


def build_parser() -> argparse.ArgumentParser:
    """Build the argument parser. Extracted for testability."""
    parser = argparse.ArgumentParser(
        description="Turbo Agent — Autonomous project management powered by Claude Agent SDK"
    )
    parser.add_argument("prompt", nargs="?", help="Task for the agent to perform")
    parser.add_argument("--project", "-p", help="Scope agent to a specific project ID")
    parser.add_argument(
        "--model",
        "-m",
        default="claude-sonnet-4-20250514",
        help="Model to use (default: claude-sonnet-4-20250514)",
    )
    parser.add_argument(
        "--max-turns",
        type=int,
        default=25,
        help="Maximum agent turns (default: 25)",
    )
    parser.add_argument(
        "--max-budget",
        type=float,
        default=2.0,
        help="Maximum budget in USD (default: 2.0)",
    )
    parser.add_argument(
        "--interactive",
        "-i",
        action="store_true",
        help="Run in interactive multi-turn mode",
    )
    parser.add_argument(
        "--stream",
        "-s",
        action="store_true",
        help="Stream agent output in real-time",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Show tool calls and debug info",
    )
    parser.add_argument(
        "--output",
        "-o",
        help="Save agent output to a file",
    )
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    # Validate inputs
    if args.max_budget <= 0:
        parser.error("--max-budget must be greater than 0")
    if args.max_turns < 1:
        parser.error("--max-turns must be at least 1")

    # Configure logging
    log_level = "DEBUG" if args.verbose else "WARNING"
    configure_agent_logging(level=log_level, json_output=not args.verbose)

    agent = TurboAgent(
        project_id=args.project,
        model=args.model,
        max_turns=args.max_turns,
        max_budget_usd=args.max_budget,
    )

    if args.interactive:
        asyncio.run(run_interactive(agent))
    elif args.prompt:
        asyncio.run(
            run_oneshot(
                agent,
                args.prompt,
                stream=args.stream,
                verbose=args.verbose,
                output_path=args.output,
            )
        )
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
