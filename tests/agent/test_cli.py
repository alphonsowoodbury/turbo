"""Tests for Turbo Agent CLI argument parsing."""

import argparse
import sys
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from turbo.agent.cli import build_parser, main, run_oneshot, run_interactive


# --- Parser Factory ---


def _make_parser() -> argparse.ArgumentParser:
    """Reconstruct the CLI parser for isolated testing.

    We rebuild it here rather than importing a parser factory because
    cli.py uses argparse directly in main(). This mirrors the actual
    parser definition.
    """
    parser = argparse.ArgumentParser(
        description="Turbo Agent -- Autonomous project management powered by Claude Agent SDK"
    )
    parser.add_argument("prompt", nargs="?", help="Task for the agent to perform")
    parser.add_argument("--project", "-p", help="Scope agent to a specific project ID")
    parser.add_argument(
        "--model",
        "-m",
        default="claude-sonnet-4-20250514",
        help="Model to use",
    )
    parser.add_argument("--max-turns", type=int, default=25, help="Maximum agent turns")
    parser.add_argument("--max-budget", type=float, default=2.0, help="Maximum budget in USD")
    parser.add_argument("--interactive", "-i", action="store_true", help="Interactive mode")
    parser.add_argument("--stream", "-s", action="store_true", help="Stream output")
    return parser


# --- Default Args ---


def test_default_args():
    parser = _make_parser()
    args = parser.parse_args(["Do something"])
    assert args.prompt == "Do something"
    assert args.project is None
    assert args.model == "claude-sonnet-4-20250514"
    assert args.max_turns == 25
    assert args.max_budget == 2.0
    assert args.interactive is False
    assert args.stream is False


# --- Flag Parsing ---


def test_project_flag():
    parser = _make_parser()
    args = parser.parse_args(["--project", "proj-123", "Do task"])
    assert args.project == "proj-123"


def test_project_short_flag():
    parser = _make_parser()
    args = parser.parse_args(["-p", "proj-456", "Do task"])
    assert args.project == "proj-456"


def test_model_flag():
    parser = _make_parser()
    args = parser.parse_args(["--model", "claude-opus-4-20250514", "Do task"])
    assert args.model == "claude-opus-4-20250514"


def test_model_short_flag():
    parser = _make_parser()
    args = parser.parse_args(["-m", "claude-haiku-3-20250307", "Do task"])
    assert args.model == "claude-haiku-3-20250307"


def test_interactive_flag():
    parser = _make_parser()
    args = parser.parse_args(["--interactive"])
    assert args.interactive is True


def test_interactive_short_flag():
    parser = _make_parser()
    args = parser.parse_args(["-i"])
    assert args.interactive is True


def test_stream_flag():
    parser = _make_parser()
    args = parser.parse_args(["--stream", "Do task"])
    assert args.stream is True


def test_stream_short_flag():
    parser = _make_parser()
    args = parser.parse_args(["-s", "Do task"])
    assert args.stream is True


def test_max_turns_flag():
    parser = _make_parser()
    args = parser.parse_args(["--max-turns", "50", "Do task"])
    assert args.max_turns == 50


def test_max_budget_flag():
    parser = _make_parser()
    args = parser.parse_args(["--max-budget", "10.0", "Do task"])
    assert args.max_budget == 10.0


# --- Budget Edge Cases ---


def test_budget_zero():
    parser = _make_parser()
    args = parser.parse_args(["--max-budget", "0", "Do task"])
    assert args.max_budget == 0.0


def test_budget_negative_parses():
    """Argparse accepts negative floats. Validation happens downstream."""
    parser = _make_parser()
    args = parser.parse_args(["--max-budget", "-1.0", "Do task"])
    assert args.max_budget == -1.0


# --- Combined Flags ---


def test_combined_flags():
    parser = _make_parser()
    args = parser.parse_args([
        "-p", "proj-1",
        "-m", "claude-opus-4-20250514",
        "--max-turns", "10",
        "--max-budget", "5.0",
        "--stream",
        "Triage all issues",
    ])
    assert args.project == "proj-1"
    assert args.model == "claude-opus-4-20250514"
    assert args.max_turns == 10
    assert args.max_budget == 5.0
    assert args.stream is True
    assert args.prompt == "Triage all issues"


# --- No Prompt, No Interactive ---


def test_no_prompt_no_interactive_exits():
    """main() with no args should call sys.exit(1)."""
    with patch("sys.argv", ["turbo-agent"]):
        with patch("turbo.agent.cli.argparse.ArgumentParser.print_help"):
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code == 1


# --- build_parser() ---


def test_build_parser_returns_parser():
    parser = build_parser()
    assert isinstance(parser, argparse.ArgumentParser)


def test_build_parser_verbose_flag():
    parser = build_parser()
    args = parser.parse_args(["--verbose", "Do task"])
    assert args.verbose is True


def test_build_parser_verbose_short_flag():
    parser = build_parser()
    args = parser.parse_args(["-v", "Do task"])
    assert args.verbose is True


def test_build_parser_output_flag():
    parser = build_parser()
    args = parser.parse_args(["--output", "report.md", "Do task"])
    assert args.output == "report.md"


def test_build_parser_output_short_flag():
    parser = build_parser()
    args = parser.parse_args(["-o", "report.md", "Do task"])
    assert args.output == "report.md"


# --- run_oneshot ---


async def test_run_oneshot_no_stream():
    """run_oneshot in non-stream mode calls agent.run and prints."""
    mock_agent = MagicMock()
    mock_agent.run = AsyncMock(return_value="Result text")
    await run_oneshot(mock_agent, "Do something")
    mock_agent.run.assert_awaited_once_with("Do something")


async def test_run_oneshot_stream_mode():
    """run_oneshot in stream mode iterates agent.stream events."""
    mock_agent = MagicMock()

    async def mock_stream(prompt):
        yield {"type": "text", "content": "Processing..."}
        yield {"type": "result", "content": {"cost": 0.01, "turns": 1}}

    mock_agent.stream = mock_stream
    await run_oneshot(mock_agent, "Do something", stream=True)


async def test_run_oneshot_stream_verbose():
    """run_oneshot in stream+verbose mode prints tool calls."""
    mock_agent = MagicMock()

    async def mock_stream(prompt):
        yield {"type": "tool_call", "content": {"name": "list_projects"}}
        yield {"type": "text", "content": "Done"}
        yield {"type": "result", "content": {"cost": 0.01, "turns": 1}}

    mock_agent.stream = mock_stream
    await run_oneshot(mock_agent, "Do something", stream=True, verbose=True)


async def test_run_oneshot_with_output(tmp_path):
    """run_oneshot saves output to file when output_path is given."""
    mock_agent = MagicMock()
    mock_agent.run = AsyncMock(return_value="Saved result")
    out_file = str(tmp_path / "out.md")
    await run_oneshot(mock_agent, "Do something", output_path=out_file)
    with open(out_file) as f:
        assert f.read() == "Saved result"


# --- main() validation ---


def test_main_invalid_budget_exits():
    """main() with --max-budget 0 should exit with error."""
    with patch("sys.argv", ["turbo-agent", "--max-budget", "0", "Do task"]):
        with pytest.raises(SystemExit) as exc_info:
            main()
        assert exc_info.value.code == 2


def test_main_invalid_max_turns_exits():
    """main() with --max-turns 0 should exit with error."""
    with patch("sys.argv", ["turbo-agent", "--max-turns", "0", "Do task"]):
        with pytest.raises(SystemExit) as exc_info:
            main()
        assert exc_info.value.code == 2


def test_main_oneshot_calls_asyncio_run():
    """main() with a prompt calls asyncio.run with run_oneshot."""
    with patch("sys.argv", ["turbo-agent", "Do task"]):
        with patch("turbo.agent.cli.asyncio.run") as mock_run:
            with patch("turbo.agent.cli.configure_agent_logging"):
                main()
                mock_run.assert_called_once()


def test_main_interactive_calls_asyncio_run():
    """main() with --interactive calls asyncio.run with run_interactive."""
    with patch("sys.argv", ["turbo-agent", "--interactive"]):
        with patch("turbo.agent.cli.asyncio.run") as mock_run:
            with patch("turbo.agent.cli.configure_agent_logging"):
                main()
                mock_run.assert_called_once()
