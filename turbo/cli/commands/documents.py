"""Document CLI commands."""

import os
import subprocess
import tempfile

import click
from rich import box
from rich.console import Console
from rich.table import Table

from turbo.cli.utils import create_document_service, create_project_service, handle_exceptions, run_async
from turbo.core.database import get_db_session
from turbo.core.schemas import DocumentCreate, DocumentUpdate
from turbo.utils.exceptions import (
    DocumentNotFoundError,
    ProjectNotFoundError,
    ValidationError,
)

console = Console()

# Valid choices for CLI options
TYPE_CHOICES = ["markdown", "text", "code", "documentation", "specification", "notes"]
FORMAT_CHOICES = ["table", "json", "csv"]
EXPORT_FORMATS = ["pdf", "html", "txt", "md"]


@click.group()
def documents_group():
    """Manage documents."""
    pass


@documents_group.command()
@click.option("--title", required=True, help="Document title")
@click.option("--content", help="Document content (or use --file)")
@click.option(
    "--file",
    "content_file",
    type=click.Path(exists=True),
    help="Read content from file",
)
@click.option("--project-id", type=click.UUID, help="Associated project ID")
@click.option(
    "--type",
    "doc_type",
    type=click.Choice(TYPE_CHOICES),
    default="markdown",
    help="Document type",
)
@click.option("--path", help="Document file path")
@handle_exceptions
def create(title, content, content_file, project_id, doc_type, path):
    """Create a new document."""

    async def _create():
        async for session in get_db_session():
            document_service = create_document_service(session)

            # Verify project exists if provided
            if project_id:
                project_service = create_project_service(session)
                try:
                    await project_service.get_project_by_id(project_id)
                except ProjectNotFoundError:
                    console.print(f"[red]Project with ID {project_id} not found[/red]")
                    return

            # Get content from file if provided
            if content_file:
                with open(content_file, encoding="utf-8") as f:
                    content = f.read()
            elif not content:
                content = ""

            document_data = DocumentCreate(
                title=title,
                content=content,
                document_type=doc_type,
                file_path=path,
                project_id=project_id,
            )

            document = await document_service.create_document(document_data)

            console.print("[green]✓[/green] Document created successfully!")
            console.print(f"  ID: {document.id}")
            console.print(f"  Title: {document.title}")
            console.print(f"  Type: {document.type}")
            if document.project_id:
                console.print(f"  Project: {document.project_id}")

            return document

    run_async(_create())


@documents_group.command()
@click.option("--project-id", type=click.UUID, help="Filter by project ID")
@click.option(
    "--type",
    "doc_type",
    type=click.Choice(TYPE_CHOICES),
    help="Filter by document type",
)
@click.option(
    "--format", type=click.Choice(FORMAT_CHOICES), default="table", help="Output format"
)
@click.option("--limit", type=int, help="Limit number of results")
@click.option("--offset", type=int, help="Offset for pagination")
@handle_exceptions
def list(project_id, doc_type, format, limit, offset):
    """List all documents."""

    async def _list():
        async for session in get_db_session():
            service = create_document_service(session)

            if project_id:
                documents = await service.get_documents_by_project(project_id)
            elif doc_type:
                documents = await service.get_documents_by_type(doc_type)
            else:
                documents = await service.get_all_documents(limit=limit, offset=offset)

            if not documents:
                console.print("[yellow]No documents found[/yellow]")
                return

            if format == "table":
                _display_documents_table(documents)
            elif format == "json":
                import json

                console.print(
                    json.dumps(
                        [d.model_dump() for d in documents], indent=2, default=str
                    )
                )
            elif format == "csv":
                _display_documents_csv(documents)

    run_async(_list())


@documents_group.command()
@click.argument("document_id", type=click.UUID)
@click.option("--detailed", is_flag=True, help="Show detailed information")
@click.option("--content", is_flag=True, help="Show document content")
@handle_exceptions
def get(document_id, detailed, content):
    """Get document by ID."""

    async def _get():
        async for session in get_db_session():
            service = create_document_service(session)

            try:
                document = await service.get_document_by_id(document_id)

                if detailed:
                    _display_document_detailed(document)
                else:
                    _display_document_summary(document)

                if content:
                    console.print("\n[bold cyan]Content:[/bold cyan]")
                    console.print("-" * 40)
                    console.print(document.content or "[dim]No content[/dim]")

            except DocumentNotFoundError:
                console.print(f"[red]Document with ID {document_id} not found[/red]")
                return

    run_async(_get())


@documents_group.command()
@click.argument("document_id", type=click.UUID)
@click.option("--title", help="Update document title")
@click.option("--content", help="Update document content")
@click.option(
    "--file",
    "content_file",
    type=click.Path(exists=True),
    help="Read content from file",
)
@click.option(
    "--type", "doc_type", type=click.Choice(TYPE_CHOICES), help="Update document type"
)
@click.option("--path", help="Update document file path")
@handle_exceptions
def update(document_id, title, content, content_file, doc_type, path):
    """Update a document."""

    async def _update():
        async for session in get_db_session():
            service = create_document_service(session)

            # Get content from file if provided
            if content_file:
                with open(content_file, encoding="utf-8") as f:
                    content = f.read()

            # Build update data from provided options
            update_data = {}
            if title:
                update_data["title"] = title
            if content is not None:
                update_data["content"] = content
            if doc_type:
                update_data["document_type"] = doc_type
            if path:
                update_data["file_path"] = path

            if not update_data:
                console.print("[yellow]No updates provided[/yellow]")
                return

            try:
                document_update = DocumentUpdate(**update_data)
                document = await service.update_document(document_id, document_update)

                console.print("[green]✓[/green] Document updated successfully!")
                _display_document_summary(document)

            except DocumentNotFoundError:
                console.print(f"[red]Document with ID {document_id} not found[/red]")
            except ValidationError as e:
                console.print(f"[red]Validation error: {e}[/red]")

    run_async(_update())


@documents_group.command()
@click.argument("document_id", type=click.UUID)
@click.option("--confirm", is_flag=True, help="Skip confirmation prompt")
@handle_exceptions
def delete(document_id, confirm):
    """Delete a document."""
    if not confirm:
        if not click.confirm("Are you sure you want to delete this document?"):
            console.print("[yellow]Operation cancelled[/yellow]")
            return

    async def _delete():
        async for session in get_db_session():
            service = create_document_service(session)

            try:
                await service.delete_document(document_id)
                console.print("[green]✓[/green] Document deleted successfully!")

            except DocumentNotFoundError:
                console.print(f"[red]Document with ID {document_id} not found[/red]")

    run_async(_delete())


@documents_group.command()
@click.argument("query")
@click.option(
    "--format", type=click.Choice(FORMAT_CHOICES), default="table", help="Output format"
)
@handle_exceptions
def search(query, format):
    """Search documents by title and content."""

    async def _search():
        async for session in get_db_session():
            service = create_document_service(session)

            documents = await service.search_documents(query)

            if not documents:
                console.print(f"[yellow]No documents found matching '{query}'[/yellow]")
                return

            console.print(
                f"[blue]Found {len(documents)} document(s) matching '{query}':[/blue]"
            )

            if format == "table":
                _display_documents_table(documents)
            elif format == "json":
                import json

                console.print(
                    json.dumps(
                        [d.model_dump() for d in documents], indent=2, default=str
                    )
                )

    run_async(_search())


@documents_group.command()
@click.argument("document_id", type=click.UUID)
@click.option(
    "--format", type=click.Choice(EXPORT_FORMATS), default="md", help="Export format"
)
@click.option("--output", type=click.Path(), help="Output file path")
@handle_exceptions
def export(document_id, format, output):
    """Export a document to different formats."""

    async def _export():
        async for session in get_db_session():
            service = create_document_service(session)

            try:
                document = await service.get_document_by_id(document_id)

                # Generate output filename if not provided
                if not output:
                    safe_title = "".join(
                        c for c in document.title if c.isalnum() or c in (" ", "-", "_")
                    ).rstrip()
                    output = f"{safe_title}.{format}"

                # Export based on format
                if format == "md":
                    content = f"# {document.title}\n\n{document.content or ''}"
                elif format == "txt":
                    content = f"{document.title}\n{'=' * len(document.title)}\n\n{document.content or ''}"
                elif format == "html":
                    content = f"<html><head><title>{document.title}</title></head><body><h1>{document.title}</h1><pre>{document.content or ''}</pre></body></html>"
                elif format == "pdf":
                    console.print(
                        "[yellow]PDF export requires additional tools (pandoc, wkhtmltopdf)[/yellow]"
                    )
                    return

                with open(output, "w", encoding="utf-8") as f:
                    f.write(content)

                console.print(f"[green]✓[/green] Document exported to {output}")

            except DocumentNotFoundError:
                console.print(f"[red]Document with ID {document_id} not found[/red]")
            except Exception as e:
                console.print(f"[red]Export failed: {e}[/red]")

    run_async(_export())


@documents_group.command()
@click.option(
    "--type",
    "doc_type",
    type=click.Choice(TYPE_CHOICES),
    default="markdown",
    help="Template type",
)
@click.option("--name", required=True, help="Template name")
@handle_exceptions
def template(doc_type, name):
    """Create a document from a template."""
    templates = {
        "markdown": {
            "readme": "# Project Name\n\n## Description\n\n## Installation\n\n## Usage\n\n## Contributing\n",
            "api_doc": "# API Documentation\n\n## Endpoints\n\n### GET /api/endpoint\n\n**Description:** \n\n**Parameters:**\n\n**Response:**\n",
            "meeting_notes": "# Meeting Notes - {date}\n\n## Attendees\n\n## Agenda\n\n## Discussion\n\n## Action Items\n",
        },
        "documentation": {
            "user_guide": "# User Guide\n\n## Overview\n\n## Getting Started\n\n## Features\n\n## Troubleshooting\n",
            "technical_spec": "# Technical Specification\n\n## Overview\n\n## Architecture\n\n## Requirements\n\n## Implementation\n",
        },
    }

    if doc_type in templates and name in templates[doc_type]:
        template_content = templates[doc_type][name]
        from datetime import datetime

        template_content = template_content.format(
            date=datetime.now().strftime("%Y-%m-%d")
        )

        console.print(f"[blue]Template '{name}' for {doc_type}:[/blue]")
        console.print("-" * 40)
        console.print(template_content)
        console.print("-" * 40)
        console.print(
            '[dim]Use \'turbo documents create --title "Title" --content "<content>"\' to create[/dim]'
        )
    else:
        console.print(
            f"[yellow]Template '{name}' not found for type '{doc_type}'[/yellow]"
        )
        console.print("[blue]Available templates:[/blue]")
        for t_type, t_templates in templates.items():
            console.print(f"  {t_type}: {', '.join(t_templates.keys())}")


@documents_group.command()
@click.argument("document_id", type=click.UUID)
@click.option("--editor", default="nano", help="Editor to use (nano, vim, code)")
@handle_exceptions
def edit(document_id, editor):
    """Edit a document in an external editor."""

    async def _edit():
        async for session in get_db_session():
            service = create_document_service(session)

            try:
                document = await service.get_document_by_id(document_id)

                # Create temporary file
                with tempfile.NamedTemporaryFile(
                    mode="w", suffix=".md", delete=False
                ) as f:
                    f.write(document.content or "")
                    temp_file = f.name

                try:
                    # Open editor
                    subprocess.run([editor, temp_file], check=True)

                    # Read updated content
                    with open(temp_file, encoding="utf-8") as f:
                        new_content = f.read()

                    # Update document if content changed
                    if new_content != (document.content or ""):
                        document_update = DocumentUpdate(content=new_content)
                        await service.update_document(document_id, document_update)
                        console.print(
                            "[green]✓[/green] Document updated successfully!"
                        )
                    else:
                        console.print("[yellow]No changes made[/yellow]")

                finally:
                    # Clean up temp file
                    os.unlink(temp_file)

            except DocumentNotFoundError:
                console.print(f"[red]Document with ID {document_id} not found[/red]")
            except subprocess.CalledProcessError:
                console.print(f"[red]Failed to open editor '{editor}'[/red]")
            except FileNotFoundError:
                console.print(f"[red]Editor '{editor}' not found[/red]")

    run_async(_edit())


def _display_documents_table(documents):
    """Display documents in table format."""
    table = Table(box=box.SIMPLE_HEAD)
    table.add_column("ID", style="dim")
    table.add_column("Title", style="bold")
    table.add_column("Type", style="cyan")
    table.add_column("Project", style="yellow")
    table.add_column("Size", style="green")
    table.add_column("Created", style="dim")

    for document in documents:
        created = (
            document.created_at.strftime("%Y-%m-%d")
            if hasattr(document.created_at, "strftime")
            else str(document.created_at)[:10]
        )
        content_size = len(document.content or "")
        size_str = (
            f"{content_size} chars"
            if content_size < 1000
            else f"{content_size/1000:.1f}K chars"
        )
        project_str = (
            str(document.project_id)[:8] + "..." if document.project_id else "None"
        )

        table.add_row(
            str(document.id)[:8] + "...",
            document.title[:40] + "..." if len(document.title) > 40 else document.title,
            document.type,
            project_str,
            size_str,
            created,
        )

    console.print(table)


def _display_documents_csv(documents):
    """Display documents in CSV format."""
    console.print("ID,Title,Type,Project,Size,Created")
    for document in documents:
        created = (
            document.created_at.strftime("%Y-%m-%d")
            if hasattr(document.created_at, "strftime")
            else str(document.created_at)[:10]
        )
        title = document.title.replace(",", ";")  # Replace commas to avoid CSV issues
        content_size = len(document.content or "")
        project_id = document.project_id or "None"
        console.print(
            f"{document.id},{title},{document.type},{project_id},{content_size},{created}"
        )


def _display_document_summary(document):
    """Display document summary."""
    console.print(f"[bold]{document.title}[/bold]")
    console.print(f"  ID: {document.id}")
    console.print(f"  Type: [cyan]{document.type}[/cyan]")
    if document.project_id:
        console.print(f"  Project: [yellow]{document.project_id}[/yellow]")
    if document.file_path:
        console.print(f"  Path: {document.file_path}")

    content_size = len(document.content or "")
    size_str = (
        f"{content_size} characters"
        if content_size < 1000
        else f"{content_size/1000:.1f}K characters"
    )
    console.print(f"  Size: [green]{size_str}[/green]")


def _display_document_detailed(document):
    """Display detailed document information."""
    table = Table(box=box.SIMPLE)
    table.add_column("Field", style="cyan")
    table.add_column("Value", style="white")

    table.add_row("ID", str(document.id))
    table.add_row("Title", document.title)
    table.add_row("Type", document.type)
    table.add_row(
        "Project ID", str(document.project_id) if document.project_id else "None"
    )
    table.add_row("File Path", document.file_path or "None")

    content_size = len(document.content or "")
    size_str = (
        f"{content_size} characters"
        if content_size < 1000
        else f"{content_size/1000:.1f}K characters"
    )
    table.add_row("Content Size", size_str)

    created = (
        document.created_at.strftime("%Y-%m-%d %H:%M:%S")
        if hasattr(document.created_at, "strftime")
        else str(document.created_at)
    )
    updated = (
        document.updated_at.strftime("%Y-%m-%d %H:%M:%S")
        if hasattr(document.updated_at, "strftime")
        else str(document.updated_at)
    )

    table.add_row("Created", created)
    table.add_row("Updated", updated)

    console.print(table)
