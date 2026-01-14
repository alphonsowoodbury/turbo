"""Database backup and restore commands."""

import subprocess
from datetime import datetime
from pathlib import Path

import click
from rich.console import Console

from turbo.utils.config import get_settings

console = Console()


@click.group()
def db():
    """Database backup and restore commands."""
    pass


@db.command()
@click.option(
    "--output",
    type=click.Path(),
    help="Output file path (default: ./backups/turbo_backup_TIMESTAMP.sql)",
)
@click.option(
    "--format",
    type=click.Choice(["sql", "custom", "tar"]),
    default="sql",
    help="Backup format (default: sql)",
)
def backup(output, format):
    """Create a database backup."""
    settings = get_settings()

    # Parse database URL to get connection details
    db_url = settings.database.url

    # Handle both SQLite and PostgreSQL
    if db_url.startswith("sqlite"):
        console.print("[yellow]SQLite backup: Copy the database file directly[/yellow]")
        # Extract file path from sqlite:///path/to/db.sqlite
        db_path = db_url.replace("sqlite:///", "").replace("sqlite+aiosqlite:///", "")
        console.print(f"Database location: {db_path}")

        if output:
            import shutil
            output_path = Path(output)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(db_path, output_path)
            console.print(f"[green]✓[/green] Database backed up to {output_path}")
        else:
            console.print(f"Use: cp {db_path} /path/to/backup.sqlite")
        return

    # PostgreSQL backup
    if not db_url.startswith("postgresql"):
        console.print(f"[red]Unsupported database type: {db_url.split(':')[0]}[/red]")
        return

    # Default output path with timestamp
    if not output:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_dir = Path("./backups")
        backup_dir.mkdir(exist_ok=True)

        if format == "sql":
            output = backup_dir / f"turbo_backup_{timestamp}.sql"
        elif format == "custom":
            output = backup_dir / f"turbo_backup_{timestamp}.dump"
        else:  # tar
            output = backup_dir / f"turbo_backup_{timestamp}.tar"

    output_path = Path(output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Parse PostgreSQL URL: postgresql://user:pass@host:port/dbname
    # or postgresql+asyncpg://user:pass@host:port/dbname
    url_parts = db_url.replace("postgresql+asyncpg://", "").replace("postgresql://", "")

    # Split credentials and host/db
    if "@" in url_parts:
        creds, host_db = url_parts.split("@", 1)
        if ":" in creds:
            user, password = creds.split(":", 1)
        else:
            user = creds
            password = ""
    else:
        console.print("[red]Invalid database URL format[/red]")
        return

    # Split host:port/dbname
    if "/" in host_db:
        host_port, dbname = host_db.split("/", 1)
    else:
        console.print("[red]Invalid database URL format[/red]")
        return

    # Split host and port
    if ":" in host_port:
        host, port = host_port.split(":", 1)
    else:
        host = host_port
        port = "5432"

    console.print(f"[blue]Creating database backup...[/blue]")
    console.print(f"  Host: {host}:{port}")
    console.print(f"  Database: {dbname}")
    console.print(f"  Format: {format}")

    try:
        # Build pg_dump command
        env = {"PGPASSWORD": password} if password else {}

        if format == "sql":
            cmd = [
                "pg_dump",
                "-h", host,
                "-p", port,
                "-U", user,
                "-d", dbname,
                "-f", str(output_path),
                "--clean",  # Include DROP statements
                "--if-exists",  # Add IF EXISTS to DROP statements
                "--no-owner",  # Don't include ownership commands
                "--no-acl",  # Don't include ACL commands
            ]
        elif format == "custom":
            cmd = [
                "pg_dump",
                "-h", host,
                "-p", port,
                "-U", user,
                "-d", dbname,
                "-f", str(output_path),
                "-Fc",  # Custom format
                "--clean",
                "--if-exists",
                "--no-owner",
                "--no-acl",
            ]
        else:  # tar
            cmd = [
                "pg_dump",
                "-h", host,
                "-p", port,
                "-U", user,
                "-d", dbname,
                "-f", str(output_path),
                "-Ft",  # Tar format
                "--clean",
                "--if-exists",
                "--no-owner",
                "--no-acl",
            ]

        result = subprocess.run(
            cmd,
            env={**subprocess.os.environ, **env},
            capture_output=True,
            text=True,
        )

        if result.returncode == 0:
            file_size = output_path.stat().st_size
            size_mb = file_size / (1024 * 1024)
            console.print(
                f"[green]✓[/green] Database backup created successfully"
            )
            console.print(f"  Location: {output_path}")
            console.print(f"  Size: {size_mb:.2f} MB")
        else:
            console.print(f"[red]Backup failed:[/red]")
            console.print(result.stderr)

    except FileNotFoundError:
        console.print(
            "[red]Error: pg_dump not found. Please install PostgreSQL client tools.[/red]"
        )
    except Exception as e:
        console.print(f"[red]Backup failed: {e}[/red]")


@db.command()
@click.argument("backup_file", type=click.Path(exists=True))
@click.option(
    "--confirm",
    is_flag=True,
    help="Confirm restoration (will overwrite existing data)",
)
def restore(backup_file, confirm):
    """Restore database from backup file."""
    if not confirm:
        console.print(
            "[yellow]WARNING: This will overwrite all existing data![/yellow]"
        )
        console.print("Use --confirm flag to proceed with restoration.")
        return

    settings = get_settings()
    db_url = settings.database.url

    # Handle SQLite
    if db_url.startswith("sqlite"):
        console.print("[yellow]SQLite restore: Replace the database file directly[/yellow]")
        db_path = db_url.replace("sqlite:///", "").replace("sqlite+aiosqlite:///", "")
        console.print(f"Database location: {db_path}")

        import shutil
        shutil.copy2(backup_file, db_path)
        console.print(f"[green]✓[/green] Database restored from {backup_file}")
        return

    # PostgreSQL restore
    if not db_url.startswith("postgresql"):
        console.print(f"[red]Unsupported database type: {db_url.split(':')[0]}[/red]")
        return

    # Parse PostgreSQL URL
    url_parts = db_url.replace("postgresql+asyncpg://", "").replace("postgresql://", "")

    if "@" in url_parts:
        creds, host_db = url_parts.split("@", 1)
        if ":" in creds:
            user, password = creds.split(":", 1)
        else:
            user = creds
            password = ""
    else:
        console.print("[red]Invalid database URL format[/red]")
        return

    if "/" in host_db:
        host_port, dbname = host_db.split("/", 1)
    else:
        console.print("[red]Invalid database URL format[/red]")
        return

    if ":" in host_port:
        host, port = host_port.split(":", 1)
    else:
        host = host_port
        port = "5432"

    backup_path = Path(backup_file)

    console.print(f"[blue]Restoring database...[/blue]")
    console.print(f"  Host: {host}:{port}")
    console.print(f"  Database: {dbname}")
    console.print(f"  From: {backup_path}")

    try:
        env = {"PGPASSWORD": password} if password else {}

        # Determine restore command based on file extension
        if backup_path.suffix == ".sql":
            cmd = [
                "psql",
                "-h", host,
                "-p", port,
                "-U", user,
                "-d", dbname,
                "-f", str(backup_path),
            ]
        else:
            # Custom or tar format
            cmd = [
                "pg_restore",
                "-h", host,
                "-p", port,
                "-U", user,
                "-d", dbname,
                "--clean",
                "--if-exists",
                "--no-owner",
                "--no-acl",
                str(backup_path),
            ]

        result = subprocess.run(
            cmd,
            env={**subprocess.os.environ, **env},
            capture_output=True,
            text=True,
        )

        if result.returncode == 0:
            console.print("[green]✓[/green] Database restored successfully")
        else:
            # pg_restore may return non-zero even on success due to warnings
            if "ERROR" in result.stderr:
                console.print(f"[red]Restore failed:[/red]")
                console.print(result.stderr)
            else:
                console.print("[green]✓[/green] Database restored successfully")
                if result.stderr:
                    console.print("[yellow]Warnings:[/yellow]")
                    console.print(result.stderr)

    except FileNotFoundError:
        console.print(
            "[red]Error: PostgreSQL client tools not found. Please install them.[/red]"
        )
    except Exception as e:
        console.print(f"[red]Restore failed: {e}[/red]")