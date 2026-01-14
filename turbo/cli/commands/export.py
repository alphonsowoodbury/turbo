"""Export command."""

import csv
from datetime import datetime
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

console = Console()

# Valid choices for CLI options
FORMAT_CHOICES = ["json", "csv", "txt"]
TYPE_CHOICES = ["all", "projects", "issues", "documents", "tags"]


@click.command()
@click.option("--output", type=click.Path(), required=True, help="Output file path")
@click.option(
    "--format", type=click.Choice(FORMAT_CHOICES), default="json", help="Export format"
)
@click.option(
    "--type",
    type=click.Choice(TYPE_CHOICES),
    default="all",
    help="Entity type to export",
)
@click.option("--include-content", is_flag=True, help="Include full document content")
@handle_exceptions
def export_command(output, format, type, include_content):
    """Export workspace data to file."""

    async def _export():
        async for session in get_db_session():
            project_service = get_project_service(session)
            issue_service = get_issue_service(session)
            document_service = get_document_service(session)
            tag_service = get_tag_service(session)

            export_data = {
                "metadata": {
                    "export_date": datetime.now().isoformat(),
                    "export_format": format,
                    "export_type": type,
                    "include_content": include_content,
                }
            }

            try:
                console.print(f"[blue]Exporting {type} data...[/blue]")

                if type in ["all", "projects"]:
                    projects = await project_service.get_all_projects()
                    export_data["projects"] = [p.model_dump() for p in projects]
                    console.print(f"  Projects: {len(projects)}")

                if type in ["all", "issues"]:
                    issues = await issue_service.get_all_issues()
                    export_data["issues"] = [i.model_dump() for i in issues]
                    console.print(f"  Issues: {len(issues)}")

                if type in ["all", "documents"]:
                    documents = await document_service.get_all_documents()
                    if include_content:
                        export_data["documents"] = [d.model_dump() for d in documents]
                    else:
                        # Export without content for smaller file size
                        export_data["documents"] = [
                            {k: v for k, v in d.model_dump().items() if k != "content"}
                            for d in documents
                        ]
                    console.print(f"  Documents: {len(documents)}")

                if type in ["all", "tags"]:
                    tags = await tag_service.get_all_tags()
                    export_data["tags"] = [t.model_dump() for t in tags]
                    console.print(f"  Tags: {len(tags)}")

                # Write to file based on format
                output_path = Path(output)
                output_path.parent.mkdir(parents=True, exist_ok=True)

                if format == "json":
                    with open(output_path, "w", encoding="utf-8") as f:
                        json.dump(export_data, f, indent=2, default=str)

                elif format == "csv":
                    _export_csv(export_data, output_path, type)

                elif format == "txt":
                    _export_txt(export_data, output_path, type)

                console.print(
                    f"[green]✓[/green] Data exported successfully to {output_path}"
                )

            except Exception as e:
                console.print(f"[red]Export failed: {e}[/red]")

    run_async(_export())


def _export_csv(export_data, output_path, export_type):
    """Export data in CSV format."""
    if export_type == "all":
        # Create separate CSV files for each entity type
        base_path = output_path.with_suffix("")

        for entity_type in ["projects", "issues", "documents", "tags"]:
            if export_data.get(entity_type):
                csv_path = base_path.parent / f"{base_path.name}_{entity_type}.csv"
                _write_entity_csv(export_data[entity_type], csv_path, entity_type)
    else:
        # Single CSV file for specific type
        entity_data = export_data.get(export_type, [])
        _write_entity_csv(entity_data, output_path, export_type)


def _write_entity_csv(data, file_path, entity_type):
    """Write entity data to CSV file."""
    if not data:
        return

    with open(file_path, "w", newline="", encoding="utf-8") as f:
        if data:
            writer = csv.DictWriter(f, fieldnames=data[0].keys())
            writer.writeheader()
            for item in data:
                # Convert datetime objects to strings
                row = {
                    k: str(v) if hasattr(v, "isoformat") else v for k, v in item.items()
                }
                writer.writerow(row)


def _export_txt(export_data, output_path, export_type):
    """Export data in text format."""
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("Turbo Workspace Export\n")
        f.write(f"Export Date: {export_data['metadata']['export_date']}\n")
        f.write(f"Export Type: {export_type}\n")
        f.write("=" * 50 + "\n\n")

        if "projects" in export_data:
            f.write("PROJECTS\n")
            f.write("-" * 20 + "\n")
            for project in export_data["projects"]:
                f.write(f"Name: {project['name']}\n")
                f.write(f"Description: {project['description']}\n")
                f.write(f"Status: {project['status']}\n")
                f.write(f"Priority: {project['priority']}\n")
                f.write(f"Completion: {project['completion_percentage']}%\n")
                f.write("\n")

        if "issues" in export_data:
            f.write("ISSUES\n")
            f.write("-" * 20 + "\n")
            for issue in export_data["issues"]:
                f.write(f"Title: {issue['title']}\n")
                f.write(f"Description: {issue['description']}\n")
                f.write(f"Status: {issue['status']}\n")
                f.write(f"Priority: {issue['priority']}\n")
                f.write(f"Type: {issue['issue_type']}\n")
                f.write(f"Assignee: {issue.get('assignee', 'Unassigned')}\n")
                f.write("\n")

        if "documents" in export_data:
            f.write("DOCUMENTS\n")
            f.write("-" * 20 + "\n")
            for document in export_data["documents"]:
                f.write(f"Title: {document['title']}\n")
                f.write(f"Type: {document['document_type']}\n")
                if "content" in document:
                    f.write(f"Content:\n{document['content']}\n")
                f.write("\n")

        if "tags" in export_data:
            f.write("TAGS\n")
            f.write("-" * 20 + "\n")
            for tag in export_data["tags"]:
                f.write(f"Name: {tag['name']}\n")
                f.write(f"Color: {tag['color']}\n")
                f.write(f"Description: {tag.get('description', '')}\n")
                f.write("\n")
