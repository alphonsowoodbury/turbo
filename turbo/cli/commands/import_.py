"""Import command."""

import csv
import json
from pathlib import Path

import click
from rich.console import Console

from turbo.api.dependencies import (
    get_document_service,
    get_issue_service,
    get_project_service,
    get_tag_service,
)
from turbo.cli.utils import handle_exceptions, run_async
from turbo.core.database import get_db_session
from turbo.core.schemas import DocumentCreate, IssueCreate, ProjectCreate, TagCreate

console = Console()

# Valid choices for CLI options
TYPE_CHOICES = ["all", "projects", "issues", "documents", "tags"]


@click.command()
@click.option(
    "--file",
    "import_file",
    type=click.Path(exists=True),
    required=True,
    help="Import file path",
)
@click.option(
    "--type",
    type=click.Choice(TYPE_CHOICES),
    default="all",
    help="Entity type to import",
)
@click.option(
    "--dry-run", is_flag=True, help="Show what would be imported without making changes"
)
@click.option("--skip-existing", is_flag=True, help="Skip items that already exist")
@handle_exceptions
def import_command(import_file, type, dry_run, skip_existing):
    """Import workspace data from file."""

    async def _import():
        async for session in get_db_session():
            project_service = get_project_service(session)
            issue_service = get_issue_service(session)
            document_service = get_document_service(session)
            tag_service = get_tag_service(session)

            try:
                import_path = Path(import_file)
                console.print(f"[blue]Importing data from {import_path}...[/blue]")

                # Load data based on file extension
                if import_path.suffix.lower() == ".json":
                    with open(import_path, encoding="utf-8") as f:
                        import_data = json.load(f)
                elif import_path.suffix.lower() == ".csv":
                    import_data = _load_csv_data(import_path, type)
                else:
                    console.print(
                        f"[red]Unsupported file format: {import_path.suffix}[/red]"
                    )
                    return

                if dry_run:
                    _show_import_preview(import_data, type)
                    return

                # Import data
                results = {}

                if type in ["all", "projects"] and "projects" in import_data:
                    results["projects"] = await _import_projects(
                        import_data["projects"], project_service, skip_existing
                    )

                if type in ["all", "issues"] and "issues" in import_data:
                    results["issues"] = await _import_issues(
                        import_data["issues"], issue_service, skip_existing
                    )

                if type in ["all", "documents"] and "documents" in import_data:
                    results["documents"] = await _import_documents(
                        import_data["documents"], document_service, skip_existing
                    )

                if type in ["all", "tags"] and "tags" in import_data:
                    results["tags"] = await _import_tags(
                        import_data["tags"], tag_service, skip_existing
                    )

                # Show results
                _show_import_results(results)

            except Exception as e:
                console.print(f"[red]Import failed: {e}[/red]")

    run_async(_import())


def _load_csv_data(file_path, import_type):
    """Load data from CSV file."""
    import_data = {}

    with open(file_path, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        data = list(reader)

    if import_type == "all":
        # Assume the CSV contains projects if type is 'all'
        import_data["projects"] = data
    else:
        import_data[import_type] = data

    return import_data


def _show_import_preview(import_data, import_type):
    """Show what would be imported."""
    console.print("[yellow]DRY RUN - Preview of import data:[/yellow]\n")

    for entity_type, items in import_data.items():
        if entity_type == "metadata":
            continue

        if import_type != "all" and entity_type != import_type:
            continue

        if items:
            console.print(f"[cyan]{entity_type.title()}:[/cyan] {len(items)} items")
            # Show first few items as examples
            for i, item in enumerate(items[:3]):
                if entity_type == "projects":
                    console.print(f"  - {item.get('name', 'Unknown')}")
                elif entity_type == "issues" or entity_type == "documents":
                    console.print(f"  - {item.get('title', 'Unknown')}")
                elif entity_type == "tags":
                    console.print(f"  - {item.get('name', 'Unknown')}")

            if len(items) > 3:
                console.print(f"  ... and {len(items) - 3} more")
            console.print()


async def _import_projects(projects_data, project_service, skip_existing):
    """Import projects."""
    imported = 0
    skipped = 0
    errors = 0

    for project_data in projects_data:
        try:
            # Check if project exists if skip_existing is True
            if skip_existing:
                try:
                    existing = await project_service.search_projects_by_name(
                        project_data["name"]
                    )
                    if existing:
                        skipped += 1
                        continue
                except:
                    pass

            # Create project
            project_create = ProjectCreate(
                name=project_data["name"],
                description=project_data.get("description", ""),
                priority=project_data.get("priority", "medium"),
                status=project_data.get("status", "active"),
                completion_percentage=float(
                    project_data.get("completion_percentage", 0)
                ),
            )

            await project_service.create_project(project_create)
            imported += 1

        except Exception as e:
            console.print(
                f"[red]Error importing project '{project_data.get('name', 'Unknown')}': {e}[/red]"
            )
            errors += 1

    return {"imported": imported, "skipped": skipped, "errors": errors}


async def _import_issues(issues_data, issue_service, skip_existing):
    """Import issues."""
    imported = 0
    skipped = 0
    errors = 0

    for issue_data in issues_data:
        try:
            # Check if issue exists if skip_existing is True
            if skip_existing:
                try:
                    existing = await issue_service.search_issues_by_title(
                        issue_data["title"]
                    )
                    if existing:
                        skipped += 1
                        continue
                except:
                    pass

            # Create issue (assuming project_id is provided or using a default)
            issue_create = IssueCreate(
                title=issue_data["title"],
                description=issue_data.get("description", ""),
                project_id=issue_data.get("project_id"),  # This might need handling
                priority=issue_data.get("priority", "medium"),
                status=issue_data.get("status", "open"),
                issue_type=issue_data.get("issue_type", "task"),
                assignee=issue_data.get("assignee"),
            )

            if issue_create.project_id:  # Only create if project_id is provided
                await issue_service.create_issue(issue_create)
                imported += 1
            else:
                console.print(
                    f"[yellow]Skipping issue '{issue_data['title']}' - no project_id[/yellow]"
                )
                skipped += 1

        except Exception as e:
            console.print(
                f"[red]Error importing issue '{issue_data.get('title', 'Unknown')}': {e}[/red]"
            )
            errors += 1

    return {"imported": imported, "skipped": skipped, "errors": errors}


async def _import_documents(documents_data, document_service, skip_existing):
    """Import documents."""
    imported = 0
    skipped = 0
    errors = 0

    for document_data in documents_data:
        try:
            # Check if document exists if skip_existing is True
            if skip_existing:
                try:
                    existing = await document_service.search_documents(
                        document_data["title"]
                    )
                    if existing:
                        skipped += 1
                        continue
                except:
                    pass

            # Create document
            document_create = DocumentCreate(
                title=document_data["title"],
                content=document_data.get("content", ""),
                document_type=document_data.get("document_type", "markdown"),
                file_path=document_data.get("file_path"),
                project_id=document_data.get("project_id"),
            )

            await document_service.create_document(document_create)
            imported += 1

        except Exception as e:
            console.print(
                f"[red]Error importing document '{document_data.get('title', 'Unknown')}': {e}[/red]"
            )
            errors += 1

    return {"imported": imported, "skipped": skipped, "errors": errors}


async def _import_tags(tags_data, tag_service, skip_existing):
    """Import tags."""
    imported = 0
    skipped = 0
    errors = 0

    for tag_data in tags_data:
        try:
            # Check if tag exists if skip_existing is True
            if skip_existing:
                try:
                    existing = await tag_service.search_tags_by_name(tag_data["name"])
                    if existing:
                        skipped += 1
                        continue
                except:
                    pass

            # Create tag
            tag_create = TagCreate(
                name=tag_data["name"],
                description=tag_data.get("description"),
                color=tag_data.get("color", "blue"),
            )

            await tag_service.create_tag(tag_create)
            imported += 1

        except Exception as e:
            console.print(
                f"[red]Error importing tag '{tag_data.get('name', 'Unknown')}': {e}[/red]"
            )
            errors += 1

    return {"imported": imported, "skipped": skipped, "errors": errors}


def _show_import_results(results):
    """Show import results summary."""
    console.print("\n[bold green]Import Summary:[/bold green]")

    total_imported = 0
    total_skipped = 0
    total_errors = 0

    for entity_type, stats in results.items():
        console.print(f"\n[cyan]{entity_type.title()}:[/cyan]")
        console.print(f"  Imported: [green]{stats['imported']}[/green]")
        if stats["skipped"] > 0:
            console.print(f"  Skipped: [yellow]{stats['skipped']}[/yellow]")
        if stats["errors"] > 0:
            console.print(f"  Errors: [red]{stats['errors']}[/red]")

        total_imported += stats["imported"]
        total_skipped += stats["skipped"]
        total_errors += stats["errors"]

    console.print("\n[bold]Total:[/bold]")
    console.print(f"  Imported: [green]{total_imported}[/green]")
    if total_skipped > 0:
        console.print(f"  Skipped: [yellow]{total_skipped}[/yellow]")
    if total_errors > 0:
        console.print(f"  Errors: [red]{total_errors}[/red]")

    if total_imported > 0:
        console.print("\n[green]✓[/green] Import completed successfully!")
    elif total_errors > 0:
        console.print("\n[red]✗[/red] Import completed with errors")
    else:
        console.print("\n[yellow]![/yellow] No items were imported")
