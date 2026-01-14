"""Initialization command."""

from pathlib import Path
import shutil

import click
from rich.console import Console

from turbo.cli.utils import handle_exceptions, run_async
from turbo.core.database import init_database

console = Console()


@click.command()
@click.option("--workspace", type=click.Path(), default=".", help="Workspace directory")
@click.option("--config", type=click.Path(exists=True), help="Configuration file")
@click.option(
    "--force", is_flag=True, help="Force initialization even if already exists"
)
@handle_exceptions
def init_command(workspace, config, force):
    """Initialize a new Turbo workspace."""
    workspace_path = Path(workspace).resolve()
    turbo_dir = workspace_path / ".turbo"

    # Check if already initialized
    if turbo_dir.exists() and not force:
        console.print(
            f"[yellow]Workspace already initialized at {workspace_path}[/yellow]"
        )
        console.print("Use --force to reinitialize")
        return

    try:
        # Create .turbo directory structure
        turbo_dir.mkdir(exist_ok=True)
        (turbo_dir / "context").mkdir(exist_ok=True)
        (turbo_dir / "templates").mkdir(exist_ok=True)
        (turbo_dir / "responses").mkdir(exist_ok=True)

        # Create default config if none provided
        if not config:
            config_content = """[database]
url = "sqlite:///turbo.db"

[api]
port = 8000
host = "localhost"

[environment]
debug = false
log_level = "INFO"
"""
            config_path = turbo_dir / "config.toml"
            with open(config_path, "w") as f:
                f.write(config_content)
        else:
            # Copy provided config
            shutil.copy2(config, turbo_dir / "config.toml")

        # Initialize database
        try:
            run_async(init_database())
            console.print(
                f"[green]✓[/green] Workspace initialized successfully at {workspace_path}"
            )
            console.print(f"  Configuration: {turbo_dir / 'config.toml'}")
            console.print("  Database initialized")
        except Exception as e:
            console.print(
                f"[yellow]Workspace created but database initialization failed: {e}[/yellow]"
            )

    except Exception as e:
        console.print(f"[red]Failed to initialize workspace: {e}[/red]")
        # Clean up on failure
        if turbo_dir.exists():
            shutil.rmtree(turbo_dir)
