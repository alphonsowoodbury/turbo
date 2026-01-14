"""Initiative CLI commands."""

import click
from rich import box
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.table import Table

from turbo.cli.utils import handle_exceptions, run_async
from turbo.core.database import get_db_session
from turbo.core.repositories import (
    DocumentRepository,
    InitiativeRepository,
    IssueRepository,
    ProjectRepository,
    TagRepository,
)
from turbo.core.schemas.initiative import InitiativeCreate, InitiativeUpdate
from turbo.core.services.initiative import InitiativeService
from turbo.utils.exceptions import InitiativeNotFoundError, ValidationError

console = Console()

# Valid choices for CLI options
STATUS_CHOICES = ["planning", "in_progress", "on_hold", "completed", "cancelled"]
FORMAT_CHOICES = ["table", "json", "csv"]


def create_initiative_service(session) -> InitiativeService:
    """Create initiative service with repositories."""
    initiative_repo = InitiativeRepository(session)
    project_repo = ProjectRepository(session)
    issue_repo = IssueRepository(session)
    tag_repo = TagRepository(session)
    document_repo = DocumentRepository(session)
    return InitiativeService(
        initiative_repo, project_repo, issue_repo, tag_repo, document_repo
    )


@click.group()
def initiatives_group():
    """Manage initiatives."""
    pass


@initiatives_group.command()
@click.option("--name", required=True, help="Initiative name")
@click.option("--description", required=True, help="Initiative description")
@click.option(
    "--status",
    type=click.Choice(STATUS_CHOICES),
    default="planning",
    help="Initiative status",
)
@click.option("--project-id", type=click.UUID, help="Associated project ID (optional)")
@click.option("--start-date", help="Start date (YYYY-MM-DD)")
@click.option("--target-date", help="Target completion date (YYYY-MM-DD)")
@handle_exceptions
def create(name, description, status, project_id, start_date, target_date):
    """Create a new initiative."""

    async def _create():
        async for session in get_db_session():
            service = create_initiative_service(session)

            # Parse dates if provided
            from datetime import datetime

            parsed_start_date = None
            parsed_target_date = None

            if start_date:
                try:
                    parsed_start_date = datetime.strptime(start_date, "%Y-%m-%d")
                except ValueError:
                    console.print(
                        "[red]Invalid start date format. Use YYYY-MM-DD[/red]"
                    )
                    return

            if target_date:
                try:
                    parsed_target_date = datetime.strptime(target_date, "%Y-%m-%d")
                except ValueError:
                    console.print(
                        "[red]Invalid target date format. Use YYYY-MM-DD[/red]"
                    )
                    return

            initiative_data = InitiativeCreate(
                name=name,
                description=description,
                status=status,
                project_id=project_id,
                start_date=parsed_start_date,
                target_date=parsed_target_date,
            )

            initiative = await service.create_initiative(initiative_data)

            console.print("[green]✓[/green] Initiative created successfully!")
            console.print(f"  ID: {initiative.id}")
            console.print(f"  Name: {initiative.name}")
            console.print(f"  Status: {initiative.status}")

            return initiative

    run_async(_create())


@initiatives_group.command()
@click.option(
    "--status", type=click.Choice(STATUS_CHOICES), help="Filter by status"
)
@click.option("--project-id", type=click.UUID, help="Filter by project")
@click.option(
    "--format", type=click.Choice(FORMAT_CHOICES), default="table", help="Output format"
)
@click.option("--limit", type=int, help="Limit number of results")
@click.option("--offset", type=int, help="Offset for pagination")
@handle_exceptions
def list(status, project_id, format, limit, offset):
    """List all initiatives."""

    async def _list():
        async for session in get_db_session():
            service = create_initiative_service(session)

            if status:
                initiatives = await service.get_initiatives_by_status(status)
            elif project_id:
                initiatives = await service.get_initiatives_by_project(project_id)
            else:
                initiatives = await service.get_all_initiatives(
                    limit=limit, offset=offset
                )

            if not initiatives:
                console.print("[yellow]No initiatives found[/yellow]")
                return

            if format == "table":
                _display_initiatives_table(initiatives)
            elif format == "json":
                import json

                console.print(
                    json.dumps([i.model_dump() for i in initiatives], indent=2, default=str)
                )
            elif format == "csv":
                _display_initiatives_csv(initiatives)

    run_async(_list())


@initiatives_group.command()
@click.argument("initiative_id", type=click.UUID)
@click.option("--detailed", is_flag=True, help="Show detailed information")
@handle_exceptions
def get(initiative_id, detailed):
    """Get initiative by ID."""

    async def _get():
        async for session in get_db_session():
            service = create_initiative_service(session)

            try:
                initiative = await service.get_initiative_by_id(initiative_id)

                if detailed:
                    _display_initiative_detailed(initiative)
                else:
                    _display_initiative_summary(initiative)

            except InitiativeNotFoundError:
                console.print(
                    f"[red]Initiative with ID {initiative_id} not found[/red]"
                )
                return

    run_async(_get())


@initiatives_group.command()
@click.argument("initiative_id", type=click.UUID)
@click.option("--name", help="Update initiative name")
@click.option("--description", help="Update initiative description")
@click.option("--status", type=click.Choice(STATUS_CHOICES), help="Update status")
@click.option("--project-id", type=click.UUID, help="Update associated project")
@click.option("--start-date", help="Update start date (YYYY-MM-DD)")
@click.option("--target-date", help="Update target date (YYYY-MM-DD)")
@handle_exceptions
def update(initiative_id, name, description, status, project_id, start_date, target_date):
    """Update an initiative."""

    async def _update():
        async for session in get_db_session():
            service = create_initiative_service(session)

            # Build update data from provided options
            update_data = {}
            if name:
                update_data["name"] = name
            if description:
                update_data["description"] = description
            if status:
                update_data["status"] = status
            if project_id:
                update_data["project_id"] = project_id

            # Parse dates if provided
            if start_date:
                try:
                    from datetime import datetime

                    update_data["start_date"] = datetime.strptime(
                        start_date, "%Y-%m-%d"
                    )
                except ValueError:
                    console.print(
                        "[red]Invalid start date format. Use YYYY-MM-DD[/red]"
                    )
                    return

            if target_date:
                try:
                    from datetime import datetime

                    update_data["target_date"] = datetime.strptime(
                        target_date, "%Y-%m-%d"
                    )
                except ValueError:
                    console.print(
                        "[red]Invalid target date format. Use YYYY-MM-DD[/red]"
                    )
                    return

            if not update_data:
                console.print("[yellow]No updates provided[/yellow]")
                return

            try:
                initiative_update = InitiativeUpdate(**update_data)
                initiative = await service.update_initiative(
                    initiative_id, initiative_update
                )

                console.print("[green]✓[/green] Initiative updated successfully!")
                _display_initiative_summary(initiative)

            except InitiativeNotFoundError:
                console.print(
                    f"[red]Initiative with ID {initiative_id} not found[/red]"
                )
            except ValidationError as e:
                console.print(f"[red]Validation error: {e}[/red]")

    run_async(_update())


@initiatives_group.command()
@click.argument("initiative_id", type=click.UUID)
@click.option("--confirm", is_flag=True, help="Skip confirmation prompt")
@handle_exceptions
def delete(initiative_id, confirm):
    """Delete an initiative."""
    if not confirm:
        if not click.confirm("Are you sure you want to delete this initiative?"):
            console.print("[yellow]Operation cancelled[/yellow]")
            return

    async def _delete():
        async for session in get_db_session():
            service = create_initiative_service(session)

            try:
                await service.delete_initiative(initiative_id)
                console.print("[green]✓[/green] Initiative deleted successfully!")

            except InitiativeNotFoundError:
                console.print(
                    f"[red]Initiative with ID {initiative_id} not found[/red]"
                )

    run_async(_delete())


@initiatives_group.command()
@click.argument("initiative_id", type=click.UUID)
@handle_exceptions
def issues(initiative_id):
    """List all issues associated with an initiative."""

    async def _issues():
        async for session in get_db_session():
            service = create_initiative_service(session)

            try:
                issues = await service.get_initiative_issues(initiative_id)

                if not issues:
                    console.print("[yellow]No issues found for this initiative[/yellow]")
                    return

                console.print(
                    f"[blue]Found {len(issues)} issue(s) for initiative {initiative_id}:[/blue]\n"
                )

                table = Table(box=box.SIMPLE_HEAD)
                table.add_column("ID", style="dim")
                table.add_column("Title", style="bold")
                table.add_column("Status", style="cyan")
                table.add_column("Priority", style="yellow")
                table.add_column("Type", style="magenta")

                for issue in issues:
                    table.add_row(
                        str(issue.id)[:8] + "...",
                        issue.title[:50] + "..." if len(issue.title) > 50 else issue.title,
                        issue.status,
                        issue.priority,
                        issue.type,
                    )

                console.print(table)

            except InitiativeNotFoundError:
                console.print(
                    f"[red]Initiative with ID {initiative_id} not found[/red]"
                )

    run_async(_issues())


def _display_initiatives_table(initiatives):
    """Display initiatives in table format."""
    table = Table(box=box.SIMPLE_HEAD)
    table.add_column("ID", style="dim")
    table.add_column("Name", style="bold")
    table.add_column("Status", style="cyan")
    table.add_column("Issues", style="green")
    table.add_column("Start Date", style="dim")
    table.add_column("Target Date", style="dim")

    for initiative in initiatives:
        start_date = (
            initiative.start_date.strftime("%Y-%m-%d")
            if initiative.start_date
            else "Not set"
        )
        target_date = (
            initiative.target_date.strftime("%Y-%m-%d")
            if initiative.target_date
            else "Not set"
        )

        table.add_row(
            str(initiative.id)[:8] + "...",
            initiative.name,
            initiative.status,
            str(initiative.issue_count),
            start_date,
            target_date,
        )

    console.print(table)


def _display_initiatives_csv(initiatives):
    """Display initiatives in CSV format."""
    console.print("ID,Name,Status,IssueCount,StartDate,TargetDate,Created")
    for initiative in initiatives:
        start_date = (
            initiative.start_date.strftime("%Y-%m-%d")
            if initiative.start_date
            else ""
        )
        target_date = (
            initiative.target_date.strftime("%Y-%m-%d")
            if initiative.target_date
            else ""
        )
        created = (
            initiative.created_at.strftime("%Y-%m-%d")
            if hasattr(initiative.created_at, "strftime")
            else str(initiative.created_at)[:10]
        )
        console.print(
            f"{initiative.id},{initiative.name},{initiative.status},{initiative.issue_count},{start_date},{target_date},{created}"
        )


def _display_initiative_summary(initiative):
    """Display initiative summary."""
    console.print(f"[bold]{initiative.name}[/bold]")
    console.print(f"  ID: {initiative.id}")
    console.print(f"  Status: [cyan]{initiative.status}[/cyan]")

    if initiative.project_id:
        console.print(f"  Project ID: {initiative.project_id}")

    if initiative.start_date:
        console.print(f"  Start Date: {initiative.start_date.strftime('%Y-%m-%d')}")
    if initiative.target_date:
        console.print(f"  Target Date: {initiative.target_date.strftime('%Y-%m-%d')}")

    console.print(f"  Associated Issues: {initiative.issue_count}")
    console.print(f"  Tags: {initiative.tag_count}")
    console.print(f"  Documents: {initiative.document_count}")

    console.print("\n[bold]Description:[/bold]")

    # Render description as markdown
    markdown = Markdown(initiative.description)
    console.print(Panel(markdown, border_style="dim", padding=(1, 2)))


def _display_initiative_detailed(initiative):
    """Display detailed initiative information."""
    table = Table(box=box.SIMPLE)
    table.add_column("Field", style="cyan")
    table.add_column("Value", style="white")

    table.add_row("ID", str(initiative.id))
    table.add_row("Name", initiative.name)
    table.add_row("Status", initiative.status)

    if initiative.project_id:
        table.add_row("Project ID", str(initiative.project_id))

    if initiative.start_date:
        table.add_row("Start Date", initiative.start_date.strftime("%Y-%m-%d"))
    else:
        table.add_row("Start Date", "Not set")

    if initiative.target_date:
        table.add_row("Target Date", initiative.target_date.strftime("%Y-%m-%d"))
    else:
        table.add_row("Target Date", "Not set")

    table.add_row("Associated Issues", str(initiative.issue_count))
    table.add_row("Tags", str(initiative.tag_count))
    table.add_row("Documents", str(initiative.document_count))

    created = (
        initiative.created_at.strftime("%Y-%m-%d %H:%M:%S")
        if hasattr(initiative.created_at, "strftime")
        else str(initiative.created_at)
    )
    updated = (
        initiative.updated_at.strftime("%Y-%m-%d %H:%M:%S")
        if hasattr(initiative.updated_at, "strftime")
        else str(initiative.updated_at)
    )

    table.add_row("Created", created)
    table.add_row("Updated", updated)

    console.print(table)
    console.print("\n[bold]Description:[/bold]")

    # Render description as markdown
    markdown = Markdown(initiative.description)
    console.print(Panel(markdown, border_style="dim", padding=(1, 2)))