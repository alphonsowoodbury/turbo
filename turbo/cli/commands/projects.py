"""Project CLI commands."""


import click
from rich import box
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.table import Table

from turbo.cli.utils import create_project_service, handle_exceptions, run_async
from turbo.core.database import get_db_session
from turbo.core.schemas import ProjectCreate, ProjectUpdate
from turbo.utils.exceptions import ProjectNotFoundError, ValidationError

console = Console()

# Valid choices for CLI options
PRIORITY_CHOICES = ["low", "medium", "high", "critical"]
STATUS_CHOICES = ["active", "on_hold", "completed", "archived"]
FORMAT_CHOICES = ["table", "json", "csv"]


@click.group()
def projects_group():
    """Manage projects."""
    pass


@projects_group.command()
@click.option("--name", required=True, help="Project name")
@click.option("--description", required=True, help="Project description")
@click.option(
    "--priority",
    type=click.Choice(PRIORITY_CHOICES),
    default="medium",
    help="Project priority",
)
@click.option(
    "--status",
    type=click.Choice(STATUS_CHOICES),
    default="active",
    help="Project status",
)
@click.option(
    "--completion",
    type=click.FloatRange(0, 100),
    default=0.0,
    help="Completion percentage",
)
@handle_exceptions
def create(name, description, priority, status, completion):
    """Create a new project."""

    async def _create():
        # Get database session and service
        async for session in get_db_session():
            service = create_project_service(session)

            project_data = ProjectCreate(
                name=name,
                description=description,
                priority=priority,
                status=status,
                completion_percentage=completion,
            )

            project = await service.create_project(project_data)

            console.print("[green]✓[/green] Project created successfully!")
            console.print(f"  ID: {project.id}")
            console.print(f"  Name: {project.name}")
            console.print(f"  Status: {project.status}")
            console.print(f"  Priority: {project.priority}")

            return project

    run_async(_create())


@projects_group.command()
@click.option("--status", type=click.Choice(STATUS_CHOICES), help="Filter by status")
@click.option(
    "--priority", type=click.Choice(PRIORITY_CHOICES), help="Filter by priority"
)
@click.option(
    "--format", type=click.Choice(FORMAT_CHOICES), default="table", help="Output format"
)
@click.option("--limit", type=int, help="Limit number of results")
@click.option("--offset", type=int, help="Offset for pagination")
@handle_exceptions
def list(status, priority, format, limit, offset):
    """List all projects."""

    async def _list():
        async for session in get_db_session():
            service = create_project_service(session)

            if status:
                projects = await service.get_projects_by_status(status)
            elif priority:
                projects = await service.get_projects_by_priority(priority)
            else:
                projects = await service.get_all_projects(limit=limit, offset=offset)

            if not projects:
                console.print("[yellow]No projects found[/yellow]")
                return

            if format == "table":
                _display_projects_table(projects)
            elif format == "json":
                import json

                console.print(json.dumps([p.model_dump() for p in projects], indent=2))
            elif format == "csv":
                _display_projects_csv(projects)

    run_async(_list())


@projects_group.command()
@click.argument("project_id", type=click.UUID)
@click.option("--detailed", is_flag=True, help="Show detailed information")
@handle_exceptions
def get(project_id, detailed):
    """Get project by ID."""

    async def _get():
        async for session in get_db_session():
            service = create_project_service(session)

            try:
                project = await service.get_project_by_id(project_id)

                if detailed:
                    _display_project_detailed(project)
                else:
                    _display_project_summary(project)

            except ProjectNotFoundError:
                console.print(f"[red]Project with ID {project_id} not found[/red]")
                return

    run_async(_get())


@projects_group.command()
@click.argument("project_id", type=click.UUID)
@click.option("--name", help="Update project name")
@click.option("--description", help="Update project description")
@click.option("--priority", type=click.Choice(PRIORITY_CHOICES), help="Update priority")
@click.option("--status", type=click.Choice(STATUS_CHOICES), help="Update status")
@click.option(
    "--completion", type=click.FloatRange(0, 100), help="Update completion percentage"
)
@handle_exceptions
def update(project_id, name, description, priority, status, completion):
    """Update a project."""

    async def _update():
        async for session in get_db_session():
            service = create_project_service(session)

            # Build update data from provided options
            update_data = {}
            if name:
                update_data["name"] = name
            if description:
                update_data["description"] = description
            if priority:
                update_data["priority"] = priority
            if status:
                update_data["status"] = status
            if completion is not None:
                update_data["completion_percentage"] = completion

            if not update_data:
                console.print("[yellow]No updates provided[/yellow]")
                return

            try:
                project_update = ProjectUpdate(**update_data)
                project = await service.update_project(project_id, project_update)

                console.print("[green]✓[/green] Project updated successfully!")
                _display_project_summary(project)

            except ProjectNotFoundError:
                console.print(f"[red]Project with ID {project_id} not found[/red]")
            except ValidationError as e:
                console.print(f"[red]Validation error: {e}[/red]")

    run_async(_update())


@projects_group.command()
@click.argument("project_id", type=click.UUID)
@click.option("--confirm", is_flag=True, help="Skip confirmation prompt")
@handle_exceptions
def delete(project_id, confirm):
    """Delete a project."""
    if not confirm:
        if not click.confirm("Are you sure you want to delete this project?"):
            console.print("[yellow]Operation cancelled[/yellow]")
            return

    async def _delete():
        async for session in get_db_session():
            service = create_project_service(session)

            try:
                await service.delete_project(project_id)
                console.print("[green]✓[/green] Project deleted successfully!")

            except ProjectNotFoundError:
                console.print(f"[red]Project with ID {project_id} not found[/red]")

    run_async(_delete())


@projects_group.command()
@click.argument("project_id", type=click.UUID)
@handle_exceptions
def archive(project_id):
    """Archive a project."""

    async def _archive():
        async for session in get_db_session():
            service = create_project_service(session)

            try:
                project = await service.archive_project(project_id)
                console.print("[green]✓[/green] Project archived successfully!")
                _display_project_summary(project)

            except ProjectNotFoundError:
                console.print(f"[red]Project with ID {project_id} not found[/red]")

    run_async(_archive())


@projects_group.command()
@click.argument("query")
@click.option(
    "--format", type=click.Choice(FORMAT_CHOICES), default="table", help="Output format"
)
@handle_exceptions
def search(query, format):
    """Search projects by name."""

    async def _search():
        async for session in get_db_session():
            service = create_project_service(session)

            projects = await service.search_projects_by_name(query)

            if not projects:
                console.print(f"[yellow]No projects found matching '{query}'[/yellow]")
                return

            console.print(
                f"[blue]Found {len(projects)} project(s) matching '{query}':[/blue]"
            )

            if format == "table":
                _display_projects_table(projects)
            elif format == "json":
                import json

                console.print(json.dumps([p.model_dump() for p in projects], indent=2))

    run_async(_search())


@projects_group.command()
@click.argument("project_id", type=click.UUID)
@handle_exceptions
def stats(project_id):
    """Get project statistics."""

    async def _stats():
        async for session in get_db_session():
            service = create_project_service(session)

            try:
                stats = await service.get_project_statistics(project_id)

                console.print(f"[blue]Statistics for project {project_id}:[/blue]")

                table = Table(box=box.SIMPLE)
                table.add_column("Metric", style="cyan")
                table.add_column("Value", style="green")

                table.add_row("Total Issues", str(stats.get("total_issues", 0)))
                table.add_row("Open Issues", str(stats.get("open_issues", 0)))
                table.add_row("Closed Issues", str(stats.get("closed_issues", 0)))
                table.add_row(
                    "Completion Rate", f"{stats.get('completion_rate', 0):.1f}%"
                )

                console.print(table)

            except ProjectNotFoundError:
                console.print(f"[red]Project with ID {project_id} not found[/red]")

    run_async(_stats())


def _display_projects_table(projects):
    """Display projects in table format."""
    table = Table(box=box.SIMPLE_HEAD)
    table.add_column("ID", style="dim")
    table.add_column("Name", style="bold")
    table.add_column("Status", style="cyan")
    table.add_column("Priority", style="yellow")
    table.add_column("Completion", style="green")
    table.add_column("Created", style="dim")

    for project in projects:
        created = (
            project.created_at.strftime("%Y-%m-%d")
            if hasattr(project.created_at, "strftime")
            else str(project.created_at)[:10]
        )
        table.add_row(
            str(project.id)[:8] + "...",
            project.name,
            project.status,
            project.priority,
            f"{project.completion_percentage:.1f}%",
            created,
        )

    console.print(table)


def _display_projects_csv(projects):
    """Display projects in CSV format."""
    console.print("ID,Name,Status,Priority,Completion,Created")
    for project in projects:
        created = (
            project.created_at.strftime("%Y-%m-%d")
            if hasattr(project.created_at, "strftime")
            else str(project.created_at)[:10]
        )
        console.print(
            f"{project.id},{project.name},{project.status},{project.priority},{project.completion_percentage},{created}"
        )


def _display_project_summary(project):
    """Display project summary."""
    console.print(f"[bold]{project.name}[/bold]")
    console.print(f"  ID: {project.id}")
    console.print(f"  Status: [cyan]{project.status}[/cyan]")
    console.print(f"  Priority: [yellow]{project.priority}[/yellow]")
    console.print(f"  Completion: [green]{project.completion_percentage:.1f}%[/green]")
    console.print("\n[bold]Description:[/bold]")

    # Render description as markdown
    markdown = Markdown(project.description)
    console.print(Panel(markdown, border_style="dim", padding=(1, 2)))


def _display_project_detailed(project):
    """Display detailed project information."""
    table = Table(box=box.SIMPLE)
    table.add_column("Field", style="cyan")
    table.add_column("Value", style="white")

    table.add_row("ID", str(project.id))
    table.add_row("Name", project.name)
    table.add_row("Status", project.status)
    table.add_row("Priority", project.priority)
    table.add_row("Completion", f"{project.completion_percentage:.1f}%")
    table.add_row("Archived", "Yes" if project.is_archived else "No")

    created = (
        project.created_at.strftime("%Y-%m-%d %H:%M:%S")
        if hasattr(project.created_at, "strftime")
        else str(project.created_at)
    )
    updated = (
        project.updated_at.strftime("%Y-%m-%d %H:%M:%S")
        if hasattr(project.updated_at, "strftime")
        else str(project.updated_at)
    )

    table.add_row("Created", created)
    table.add_row("Updated", updated)

    console.print(table)
    console.print("\n[bold]Description:[/bold]")

    # Render description as markdown
    markdown = Markdown(project.description)
    console.print(Panel(markdown, border_style="dim", padding=(1, 2)))
