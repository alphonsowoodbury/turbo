"""Model Context Protocol (MCP) server commands for Claude Code integration."""

import json
import os
import subprocess
import sys
from pathlib import Path

import click
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax

from turbo.cli.utils import handle_exceptions

console = Console()


@click.group()
def mcp_group():
    """Claude Code integration via MCP."""
    pass


@mcp_group.command()
@click.option(
    "--port",
    type=int,
    default=None,
    help="API port (default: from TURBO_API_URL env var or 8001)",
)
@handle_exceptions
def start(port):
    """Start the Turbo MCP server for Claude Code.

    The MCP server exposes Turbo functionality to Claude Code through
    the Model Context Protocol. This allows Claude to natively interact
    with your projects, issues, discoveries, and more.
    """
    try:
        # Set API URL environment variable
        if port:
            os.environ["TURBO_API_URL"] = f"http://localhost:{port}/api/v1"

        # Get the path to the MCP server script
        mcp_server_path = Path(__file__).parent.parent.parent / "mcp_server.py"

        if not mcp_server_path.exists():
            console.print(f"[red]Error: MCP server not found at {mcp_server_path}[/red]")
            sys.exit(1)

        console.print("[blue]Starting Turbo MCP server...[/blue]")
        console.print(f"[dim]Server: {mcp_server_path}[/dim]")
        console.print(f"[dim]API: {os.environ.get('TURBO_API_URL', 'http://localhost:8001/api/v1')}[/dim]")
        console.print()
        console.print("[yellow]Press Ctrl+C to stop[/yellow]")
        console.print()

        # Run the MCP server
        result = subprocess.run(
            [sys.executable, str(mcp_server_path)],
            env=os.environ.copy(),
        )

        if result.returncode != 0:
            console.print(f"[red]MCP server exited with code {result.returncode}[/red]")
            sys.exit(result.returncode)

    except KeyboardInterrupt:
        console.print("\n[yellow]MCP server stopped[/yellow]")
    except Exception as e:
        console.print(f"[red]Failed to start MCP server: {e}[/red]")
        sys.exit(1)


@mcp_group.command()
@click.option(
    "--format",
    type=click.Choice(["text", "json"]),
    default="text",
    help="Output format",
)
@handle_exceptions
def configure(format):
    """Show configuration for Claude Code.

    Displays the MCP server configuration that should be added to
    Claude Code's MCP settings file (~/.claude/mcp.json).
    """
    try:
        # Get the path to the MCP server script
        mcp_server_path = Path(__file__).parent.parent.parent / "mcp_server.py"
        mcp_server_path = mcp_server_path.resolve()

        # Create MCP configuration
        mcp_config = {
            "mcpServers": {
                "turbo": {
                    "command": sys.executable,
                    "args": [str(mcp_server_path)],
                    "env": {
                        "TURBO_API_URL": os.environ.get(
                            "TURBO_API_URL", "http://localhost:8001/api/v1"
                        )
                    },
                }
            }
        }

        if format == "json":
            console.print(json.dumps(mcp_config, indent=2))
        else:
            console.print(
                Panel(
                    "[bold]Claude Code MCP Configuration[/bold]\n\n"
                    "Add this configuration to [cyan]~/.claude/mcp.json[/cyan]:",
                    title="🔧 Setup Instructions",
                    border_style="blue",
                )
            )
            console.print()

            # Display the JSON configuration with syntax highlighting
            syntax = Syntax(
                json.dumps(mcp_config, indent=2),
                "json",
                theme="monokai",
                line_numbers=False,
            )
            console.print(syntax)
            console.print()

            # Show setup steps
            console.print("[bold]Setup Steps:[/bold]")
            console.print("1. Create or edit [cyan]~/.claude/mcp.json[/cyan]")
            console.print("2. Add the configuration above to the file")
            console.print("3. Restart Claude Code")
            console.print("4. Verify connection: Ask Claude to list your projects")
            console.print()

            # Show example usage
            console.print("[bold]Example Usage:[/bold]")
            console.print('  Ask Claude: [green]"Show me all active projects"[/green]')
            console.print('  Ask Claude: [green]"What are the high priority issues?"[/green]')
            console.print('  Ask Claude: [green]"List all discovery issues that need research"[/green]')

    except Exception as e:
        console.print(f"[red]Failed to generate configuration: {e}[/red]")
        sys.exit(1)


@mcp_group.command()
@handle_exceptions
def tools():
    """List all available MCP tools.

    Shows all the tools that Claude Code can use to interact with Turbo
    through the MCP server.
    """
    try:
        tools_list = [
            ("list_projects", "Get all projects with optional filtering"),
            ("get_project", "Get detailed information about a specific project"),
            ("get_project_issues", "Get all issues for a specific project"),
            ("list_issues", "Get all issues with optional filtering"),
            ("get_issue", "Get detailed information about a specific issue"),
            ("create_issue", "Create a new issue"),
            ("update_issue", "Update an issue's details"),
            ("list_discoveries", "Get all discovery issues"),
            ("list_initiatives", "Get all initiatives"),
            ("get_initiative", "Get detailed information about a specific initiative"),
            ("get_initiative_issues", "Get all issues associated with an initiative"),
            ("list_milestones", "Get all milestones"),
            ("get_milestone", "Get detailed information about a specific milestone"),
            ("get_milestone_issues", "Get all issues associated with a milestone"),
        ]

        console.print(
            Panel(
                "[bold]Available MCP Tools[/bold]\n\n"
                "These tools are automatically available to Claude Code\n"
                "when the MCP server is configured.",
                title="🛠️  Turbo MCP Tools",
                border_style="blue",
            )
        )
        console.print()

        for tool_name, description in tools_list:
            console.print(f"[cyan]{tool_name:30}[/cyan] {description}")

        console.print()
        console.print(f"[dim]Total: {len(tools_list)} tools[/dim]")

    except Exception as e:
        console.print(f"[red]Failed to list tools: {e}[/red]")
        sys.exit(1)


@mcp_group.command()
@handle_exceptions
def test():
    """Test the MCP server connection.

    Verifies that the MCP server can connect to the Turbo API
    and retrieve data successfully.
    """
    import asyncio

    import httpx

    async def test_connection():
        api_url = os.environ.get("TURBO_API_URL", "http://localhost:8001/api/v1")

        console.print("[blue]Testing Turbo API connection...[/blue]")
        console.print(f"[dim]API URL: {api_url}[/dim]")
        console.print()

        try:
            async with httpx.AsyncClient() as client:
                # Test projects endpoint
                response = await client.get(f"{api_url}/projects/")
                response.raise_for_status()
                projects = response.json()
                console.print(f"[green]✓[/green] Projects endpoint: {len(projects)} projects found")

                # Test issues endpoint
                response = await client.get(f"{api_url}/issues/")
                response.raise_for_status()
                issues = response.json()
                console.print(f"[green]✓[/green] Issues endpoint: {len(issues)} issues found")

                # Test initiatives endpoint
                response = await client.get(f"{api_url}/initiatives/")
                response.raise_for_status()
                initiatives = response.json()
                console.print(f"[green]✓[/green] Initiatives endpoint: {len(initiatives)} initiatives found")

                console.print()
                console.print("[green]✓ All tests passed! MCP server should work correctly.[/green]")

        except httpx.ConnectError:
            console.print("[red]✗ Connection failed: Could not connect to Turbo API[/red]")
            console.print("[yellow]Make sure the Turbo API is running:[/yellow]")
            console.print("  docker-compose up -d api")
            sys.exit(1)
        except Exception as e:
            console.print(f"[red]✗ Test failed: {e}[/red]")
            sys.exit(1)

    try:
        asyncio.run(test_connection())
    except Exception as e:
        console.print(f"[red]Failed to run tests: {e}[/red]")
        sys.exit(1)
