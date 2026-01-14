"""Issue CLI commands."""


import click
from rich import box
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.table import Table

from turbo.cli.utils import (
    create_issue_service,
    create_project_service,
    handle_exceptions,
    run_async,
)
from turbo.core.database import get_db_session
from turbo.core.schemas import IssueCreate, IssueUpdate
from turbo.utils.exceptions import (
    IssueNotFoundError,
    ProjectNotFoundError,
    ValidationError,
)

console = Console()

# Valid choices for CLI options
PRIORITY_CHOICES = ["low", "medium", "high", "critical"]
STATUS_CHOICES = ["open", "in_progress", "review", "testing", "closed"]
TYPE_CHOICES = ["bug", "feature", "enhancement", "task", "documentation"]
FORMAT_CHOICES = ["table", "json", "csv"]


@click.group()
def issues_group():
    """Manage issues."""
    pass


@issues_group.command()
@click.option("--title", required=True, help="Issue title")
@click.option("--description", required=True, help="Issue description")
@click.option("--project-id", type=click.UUID, required=True, help="Project ID")
@click.option(
    "--priority",
    type=click.Choice(PRIORITY_CHOICES),
    default="medium",
    help="Issue priority",
)
@click.option(
    "--status", type=click.Choice(STATUS_CHOICES), default="open", help="Issue status"
)
@click.option(
    "--type",
    "issue_type",
    type=click.Choice(TYPE_CHOICES),
    default="task",
    help="Issue type",
)
@click.option("--assignee", help="Assignee name")
@handle_exceptions
def create(title, description, project_id, priority, status, issue_type, assignee):
    """Create a new issue."""

    async def _create():
        async for session in get_db_session():
            issue_service = create_issue_service(session)
            project_service = create_project_service(session)

            # Verify project exists
            try:
                await project_service.get_project_by_id(project_id)
            except ProjectNotFoundError:
                console.print(f"[red]Project with ID {project_id} not found[/red]")
                return

            issue_data = IssueCreate(
                title=title,
                description=description,
                project_id=project_id,
                priority=priority,
                status=status,
                type=issue_type,
                assignee=assignee,
            )

            issue = await issue_service.create_issue(issue_data)

            console.print("[green]✓[/green] Issue created successfully!")
            console.print(f"  ID: {issue.id}")
            console.print(f"  Title: {issue.title}")
            console.print(f"  Status: {issue.status}")
            console.print(f"  Priority: {issue.priority}")
            console.print(f"  Type: {issue.type}")

            return issue

    run_async(_create())


@issues_group.command()
@click.option("--project-id", type=click.UUID, help="Filter by project ID")
@click.option("--status", type=click.Choice(STATUS_CHOICES), help="Filter by status")
@click.option(
    "--priority", type=click.Choice(PRIORITY_CHOICES), help="Filter by priority"
)
@click.option("--assignee", help="Filter by assignee")
@click.option(
    "--format", type=click.Choice(FORMAT_CHOICES), default="table", help="Output format"
)
@click.option("--limit", type=int, help="Limit number of results")
@click.option("--offset", type=int, help="Offset for pagination")
@handle_exceptions
def list(project_id, status, priority, assignee, format, limit, offset):
    """List all issues."""

    async def _list():
        async for session in get_db_session():
            service = create_issue_service(session)

            if project_id:
                issues = await service.get_issues_by_project(project_id)
            elif status:
                issues = await service.get_issues_by_status(status)
            elif priority:
                issues = await service.get_issues_by_priority(priority)
            elif assignee:
                issues = await service.get_issues_by_assignee(assignee)
            else:
                issues = await service.get_all_issues(limit=limit, offset=offset)

            if not issues:
                console.print("[yellow]No issues found[/yellow]")
                return

            if format == "table":
                _display_issues_table(issues)
            elif format == "json":
                import json

                console.print(
                    json.dumps([i.model_dump() for i in issues], indent=2, default=str)
                )
            elif format == "csv":
                _display_issues_csv(issues)

    run_async(_list())


@issues_group.command()
@click.argument("issue_id", type=click.UUID)
@click.option("--detailed", is_flag=True, help="Show detailed information")
@handle_exceptions
def get(issue_id, detailed):
    """Get issue by ID."""

    async def _get():
        async for session in get_db_session():
            service = create_issue_service(session)

            try:
                issue = await service.get_issue_by_id(issue_id)

                if detailed:
                    _display_issue_detailed(issue)
                else:
                    _display_issue_summary(issue)

            except IssueNotFoundError:
                console.print(f"[red]Issue with ID {issue_id} not found[/red]")
                return

    run_async(_get())


@issues_group.command()
@click.argument("issue_id", type=click.UUID)
@click.option("--title", help="Update issue title")
@click.option("--description", help="Update issue description")
@click.option("--priority", type=click.Choice(PRIORITY_CHOICES), help="Update priority")
@click.option("--status", type=click.Choice(STATUS_CHOICES), help="Update status")
@click.option(
    "--issue_type",
    "issue_type",
    type=click.Choice(TYPE_CHOICES),
    help="Update issue issue_type",
)
@click.option("--assignee", help="Update assignee")
@handle_exceptions
def update(issue_id, title, description, priority, status, issue_type, assignee):
    """Update an issue."""

    async def _update():
        async for session in get_db_session():
            service = create_issue_service(session)

            # Build update data from provided options
            update_data = {}
            if title:
                update_data["title"] = title
            if description:
                update_data["description"] = description
            if priority:
                update_data["priority"] = priority
            if status:
                update_data["status"] = status
            if issue_type:
                update_data["type"] = issue_type
            if assignee:
                update_data["assignee"] = assignee

            if not update_data:
                console.print("[yellow]No updates provided[/yellow]")
                return

            try:
                issue_update = IssueUpdate(**update_data)
                issue = await service.update_issue(issue_id, issue_update)

                console.print("[green]✓[/green] Issue updated successfully!")
                _display_issue_summary(issue)

            except IssueNotFoundError:
                console.print(f"[red]Issue with ID {issue_id} not found[/red]")
            except ValidationError as e:
                console.print(f"[red]Validation error: {e}[/red]")

    run_async(_update())


@issues_group.command()
@click.argument("issue_id", type=click.UUID)
@click.argument("assignee")
@handle_exceptions
def assign(issue_id, assignee):
    """Assign an issue to someone."""

    async def _assign():
        async for session in get_db_session():
            service = create_issue_service(session)

            try:
                issue_update = IssueUpdate(assignee=assignee)
                issue = await service.update_issue(issue_id, issue_update)

                console.print(
                    f"[green]✓[/green] Issue assigned to {assignee} successfully!"
                )
                _display_issue_summary(issue)

            except IssueNotFoundError:
                console.print(f"[red]Issue with ID {issue_id} not found[/red]")

    run_async(_assign())


@issues_group.command()
@click.argument("issue_id", type=click.UUID)
@click.option("--resolution", help="Resolution description")
@handle_exceptions
def close(issue_id, resolution):
    """Close an issue."""

    async def _close():
        async for session in get_db_session():
            service = create_issue_service(session)

            try:
                update_data = {"status": "closed"}
                if resolution:
                    # Add resolution to description or create a resolution field
                    issue = await service.get_issue_by_id(issue_id)
                    current_desc = issue.description or ""
                    update_data["description"] = (
                        f"{current_desc}\n\nResolution: {resolution}".strip()
                    )

                issue_update = IssueUpdate(**update_data)
                issue = await service.update_issue(issue_id, issue_update)

                console.print("[green]✓[/green] Issue closed successfully!")
                _display_issue_summary(issue)

            except IssueNotFoundError:
                console.print(f"[red]Issue with ID {issue_id} not found[/red]")

    run_async(_close())


@issues_group.command()
@click.argument("issue_id", type=click.UUID)
@handle_exceptions
def reopen(issue_id):
    """Reopen a closed issue."""

    async def _reopen():
        async for session in get_db_session():
            service = create_issue_service(session)

            try:
                issue_update = IssueUpdate(status="open")
                issue = await service.update_issue(issue_id, issue_update)

                console.print("[green]✓[/green] Issue reopened successfully!")
                _display_issue_summary(issue)

            except IssueNotFoundError:
                console.print(f"[red]Issue with ID {issue_id} not found[/red]")

    run_async(_reopen())


@issues_group.command()
@click.argument("issue_id", type=click.UUID)
@click.option("--confirm", is_flag=True, help="Skip confirmation prompt")
@handle_exceptions
def delete(issue_id, confirm):
    """Delete an issue."""
    if not confirm:
        if not click.confirm("Are you sure you want to delete this issue?"):
            console.print("[yellow]Operation cancelled[/yellow]")
            return

    async def _delete():
        async for session in get_db_session():
            service = create_issue_service(session)

            try:
                await service.delete_issue(issue_id)
                console.print("[green]✓[/green] Issue deleted successfully!")

            except IssueNotFoundError:
                console.print(f"[red]Issue with ID {issue_id} not found[/red]")

    run_async(_delete())


@issues_group.command()
@click.argument("query")
@click.option(
    "--format", type=click.Choice(FORMAT_CHOICES), default="table", help="Output format"
)
@handle_exceptions
def search(query, format):
    """Search issues by title."""

    async def _search():
        async for session in get_db_session():
            service = create_issue_service(session)

            issues = await service.search_issues_by_title(query)

            if not issues:
                console.print(f"[yellow]No issues found matching '{query}'[/yellow]")
                return

            console.print(
                f"[blue]Found {len(issues)} issue(s) matching '{query}':[/blue]"
            )

            if format == "table":
                _display_issues_table(issues)
            elif format == "json":
                import json

                console.print(
                    json.dumps([i.model_dump() for i in issues], indent=2, default=str)
                )

    run_async(_search())


@issues_group.command()
@click.argument("project_id", type=click.UUID)
@handle_exceptions
def stats(project_id):
    """Get issue statistics for a project."""

    async def _stats():
        async for session in get_db_session():
            service = create_issue_service(session)

            try:
                stats = await service.get_project_issue_statistics(project_id)

                console.print(
                    f"[blue]Issue statistics for project {project_id}:[/blue]"
                )

                table = Table(box=box.SIMPLE)
                table.add_column("Metric", style="cyan")
                table.add_column("Value", style="green")

                table.add_row("Total Issues", str(stats.get("total_issues", 0)))
                table.add_row("Open Issues", str(stats.get("open_issues", 0)))
                table.add_row("In Progress", str(stats.get("in_progress_issues", 0)))
                table.add_row("Resolved Issues", str(stats.get("resolved_issues", 0)))
                table.add_row("Closed Issues", str(stats.get("closed_issues", 0)))

                # Priority breakdown
                table.add_row("", "")  # Empty row
                table.add_row(
                    "Critical Priority", str(stats.get("critical_priority", 0))
                )
                table.add_row("High Priority", str(stats.get("high_priority", 0)))
                table.add_row("Medium Priority", str(stats.get("medium_priority", 0)))
                table.add_row("Low Priority", str(stats.get("low_priority", 0)))

                console.print(table)

            except ProjectNotFoundError:
                console.print(f"[red]Project with ID {project_id} not found[/red]")

    run_async(_stats())


def _display_issues_table(issues):
    """Display issues in table format."""
    table = Table(box=box.SIMPLE_HEAD)
    table.add_column("ID", style="dim")
    table.add_column("Title", style="bold")
    table.add_column("Status", style="cyan")
    table.add_column("Priority", style="yellow")
    table.add_column("Type", style="magenta")
    table.add_column("Assignee", style="green")
    table.add_column("Created", style="dim")

    for issue in issues:
        created = (
            issue.created_at.strftime("%Y-%m-%d")
            if hasattr(issue.created_at, "strftime")
            else str(issue.created_at)[:10]
        )
        table.add_row(
            str(issue.id)[:8] + "...",
            issue.title[:50] + "..." if len(issue.title) > 50 else issue.title,
            issue.status,
            issue.priority,
            issue.type,
            issue.assignee or "Unassigned",
            created,
        )

    console.print(table)


def _display_issues_csv(issues):
    """Display issues in CSV format."""
    console.print("ID,Title,Status,Priority,Type,Assignee,Project,Created")
    for issue in issues:
        created = (
            issue.created_at.strftime("%Y-%m-%d")
            if hasattr(issue.created_at, "strftime")
            else str(issue.created_at)[:10]
        )
        title = issue.title.replace(",", ";")  # Replace commas to avoid CSV issues
        assignee = issue.assignee or "Unassigned"
        console.print(
            f"{issue.id},{title},{issue.status},{issue.priority},{issue.type},{assignee},{issue.project_id},{created}"
        )


def _display_issue_summary(issue):
    """Display issue summary."""
    console.print(f"[bold]{issue.title}[/bold]")
    console.print(f"  ID: {issue.id}")
    console.print(f"  Status: [cyan]{issue.status}[/cyan]")
    console.print(f"  Priority: [yellow]{issue.priority}[/yellow]")
    console.print(f"  Type: [magenta]{issue.type}[/magenta]")
    console.print(f"  Assignee: [green]{issue.assignee or 'Unassigned'}[/green]")
    console.print(f"  Project: {issue.project_id}")
    console.print("\n[bold]Description:[/bold]")

    # Render description as markdown
    markdown = Markdown(issue.description)
    console.print(Panel(markdown, border_style="dim", padding=(1, 2)))


def _display_issue_detailed(issue):
    """Display detailed issue information."""
    table = Table(box=box.SIMPLE)
    table.add_column("Field", style="cyan")
    table.add_column("Value", style="white")

    table.add_row("ID", str(issue.id))
    table.add_row("Title", issue.title)
    table.add_row("Status", issue.status)
    table.add_row("Priority", issue.priority)
    table.add_row("Type", issue.type)
    table.add_row("Assignee", issue.assignee or "Unassigned")
    table.add_row("Project ID", str(issue.project_id))

    created = (
        issue.created_at.strftime("%Y-%m-%d %H:%M:%S")
        if hasattr(issue.created_at, "strftime")
        else str(issue.created_at)
    )
    updated = (
        issue.updated_at.strftime("%Y-%m-%d %H:%M:%S")
        if hasattr(issue.updated_at, "strftime")
        else str(issue.updated_at)
    )

    table.add_row("Created", created)
    table.add_row("Updated", updated)

    console.print(table)
    console.print("\n[bold]Description:[/bold]")

    # Render description as markdown
    markdown = Markdown(issue.description)
    console.print(Panel(markdown, border_style="dim", padding=(1, 2)))
