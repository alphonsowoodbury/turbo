"""Main CLI application entry point."""

import logging
import sys

import click
from rich.console import Console
from rich.logging import RichHandler

# Global console for rich output
console = Console()


def setup_logging(verbose: bool, quiet: bool, debug: bool):
    """Set up logging configuration."""
    if quiet:
        level = logging.ERROR
    elif verbose:
        level = logging.INFO
    elif debug:
        level = logging.DEBUG
    else:
        level = logging.WARNING

    logging.basicConfig(
        level=level,
        format="%(message)s",
        datefmt="[%X]",
        handlers=[RichHandler(console=console, rich_tracebacks=True)],
    )


@click.group(invoke_without_command=True)
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose output")
@click.option("--quiet", "-q", is_flag=True, help="Enable quiet output")
@click.option("--debug", is_flag=True, help="Enable debug output")
@click.option("--version", is_flag=True, help="Show version and exit")
@click.pass_context
def cli(ctx, verbose, quiet, debug, version):
    """
    Turbo - AI-powered local project management and development platform.

    Manage projects, issues, documents, and tags with ease.
    """
    # Ensure that ctx.obj exists and is a dict
    ctx.ensure_object(dict)

    # Store global options in context
    ctx.obj["verbose"] = verbose
    ctx.obj["quiet"] = quiet
    ctx.obj["debug"] = debug

    # Set up logging
    setup_logging(verbose, quiet, debug)

    if version:
        click.echo("Turbo CLI v1.0.0")
        sys.exit(0)

    # If no command is provided, show help
    if ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())


# Add all command groups (import locally to avoid circular imports)
def _register_commands():
    """Register all CLI commands."""
    from turbo.cli.commands.agents import agents_group
    from turbo.cli.commands.completion import completion_command
    from turbo.cli.commands.config import config_group
    from turbo.cli.commands.db import db
    from turbo.cli.commands.documents import documents_group
    from turbo.cli.commands.export import export_command
    from turbo.cli.commands.import_ import import_command
    from turbo.cli.commands.init import init_command
    from turbo.cli.commands.initiatives import initiatives_group
    from turbo.cli.commands.issues import issues_group
    from turbo.cli.commands.mcp import mcp_group
    from turbo.cli.commands.projects import projects_group
    from turbo.cli.commands.search import search_command
    from turbo.cli.commands.status import status_command
    from turbo.cli.commands.tags import tags_group

    cli.add_command(projects_group, name="projects")
    cli.add_command(issues_group, name="issues")
    cli.add_command(initiatives_group, name="initiatives")
    cli.add_command(documents_group, name="documents")
    cli.add_command(tags_group, name="tags")
    cli.add_command(agents_group, name="agents")
    cli.add_command(init_command, name="init")
    cli.add_command(config_group, name="config")
    cli.add_command(db, name="db")
    cli.add_command(mcp_group, name="mcp")
    cli.add_command(status_command, name="status")
    cli.add_command(search_command, name="search")
    cli.add_command(export_command, name="export")
    cli.add_command(import_command, name="import")
    cli.add_command(completion_command, name="completion")


# Register commands
_register_commands()


if __name__ == "__main__":
    cli()
