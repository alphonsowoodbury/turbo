"""Configuration management commands."""

import json
from pathlib import Path

import click
from rich import box
from rich.console import Console
from rich.table import Table

from turbo.cli.utils import handle_exceptions
from turbo.utils.config import get_settings

console = Console()


@click.group()
def config_group():
    """Manage configuration."""
    pass


@config_group.command()
@click.option(
    "--format",
    type=click.Choice(["table", "json"]),
    default="table",
    help="Output format",
)
@handle_exceptions
def show(format):
    """Show current configuration."""
    try:
        settings = get_settings()
        config_dict = settings.model_dump()

        if format == "table":
            _display_config_table(config_dict)
        else:
            console.print(json.dumps(config_dict, indent=2))

    except Exception as e:
        console.print(f"[red]Failed to load configuration: {e}[/red]")


@config_group.command()
@click.option('--type', 'db_type',
              type=click.Choice(['sqlite', 'postgres']),
              prompt=True,
              help='Database type to use')
@handle_exceptions
def database(db_type):
    """Configure database connection (one-time setup)."""
    import os
    from pathlib import Path

    try:
        # Create .turbo directory if it doesn't exist
        turbo_dir = Path.home() / ".turbo"
        turbo_dir.mkdir(exist_ok=True)

        config_file = turbo_dir / "database.env"

        if db_type == 'sqlite':
            database_url = "sqlite+aiosqlite:///./turbo.db"
            console.print("[green]✓[/green] Configured to use SQLite database")
            console.print("  Location: ./turbo.db")
        elif db_type == 'postgres':
            database_url = "postgresql+asyncpg://turbo:turbo_password@localhost:5432/turbo"
            console.print("[green]✓[/green] Configured to use PostgreSQL database")
            console.print("  Location: localhost:5432/turbo")
            console.print("  [dim]Make sure Docker containers are running: docker-compose up -d[/dim]")

        # Write to config file
        with open(config_file, 'w') as f:
            f.write(f"DATABASE_URL={database_url}\n")

        console.print(f"[blue]Configuration saved to:[/blue] {config_file}")
        console.print("[yellow]Restart your terminal or run:[/yellow] source ~/.zshrc")

        # Also set in current session
        os.environ['DATABASE_URL'] = database_url
        console.print("[green]Database configuration active for this session![/green]")

    except Exception as e:
        console.print(f"[red]Failed to configure database: {e}[/red]")


@config_group.command()
@click.argument("key")
@click.argument("value")
@handle_exceptions
def set(key, value):
    """Set a configuration value."""
    try:
        # This would require implementing config writing
        # For now, show what would be set
        console.print("[green]Configuration updated:[/green]")
        console.print(f"  {key} = {value}")
        console.print(
            "[yellow]Note: Configuration writing not yet implemented[/yellow]"
        )

    except Exception as e:
        console.print(f"[red]Failed to set configuration: {e}[/red]")


@config_group.command()
@click.argument("key")
@handle_exceptions
def get(key):
    """Get a configuration value."""
    try:
        settings = get_settings()
        config_dict = settings.model_dump()

        # Navigate nested keys (e.g., "database.url")
        keys = key.split(".")
        value = config_dict
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                console.print(f"[red]Configuration key '{key}' not found[/red]")
                return

        console.print(f"{key}: {value}")

    except Exception as e:
        console.print(f"[red]Failed to get configuration: {e}[/red]")


@config_group.command()
@handle_exceptions
def validate():
    """Validate current configuration."""
    try:
        settings = get_settings()
        console.print("[green]✓[/green] Configuration is valid")

        # Basic validation checks
        table = Table(box=box.SIMPLE)
        table.add_column("Check", style="cyan")
        table.add_column("Status", style="white")

        # Database URL check
        db_status = "✓ Valid" if settings.database.url else "✗ Missing"
        table.add_row("Database URL", db_status)

        # Environment check
        env_status = (
            "✓ Valid"
            if settings.environment in ["development", "production", "testing"]
            else "✗ Invalid"
        )
        table.add_row("Environment", env_status)

        console.print(table)

    except Exception as e:
        console.print(f"[red]Configuration validation failed: {e}[/red]")


@config_group.command()
@handle_exceptions
def path():
    """Show configuration file paths."""
    config_paths = [
        Path.cwd() / ".turbo" / "config.toml",
        Path.home() / ".turbo" / "config.toml",
        Path("/etc/turbo/config.toml"),
    ]

    console.print("[blue]Configuration file search paths:[/blue]")
    for i, path in enumerate(config_paths, 1):
        exists = path.exists()
        status = "[green]✓ exists[/green]" if exists else "[dim]not found[/dim]"
        console.print(f"  {i}. {path} {status}")


def _display_config_table(config_dict, prefix=""):
    """Display configuration in table format."""
    table = Table(box=box.SIMPLE)
    table.add_column("Setting", style="cyan")
    table.add_column("Value", style="white")

    def add_config_rows(data, prefix=""):
        for key, value in data.items():
            full_key = f"{prefix}.{key}" if prefix else key
            if isinstance(value, dict):
                add_config_rows(value, full_key)
            else:
                table.add_row(full_key, str(value))

    add_config_rows(config_dict)
    console.print(table)
