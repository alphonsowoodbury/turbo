#!/usr/bin/env python3
"""
Migrate all markdown files from docs/ directory to Turbo Documents.

This script:
1. Finds all .md files in docs/ directory
2. Maps them to appropriate document types
3. Creates Turbo Documents with the content
4. Stores them in the database with proper metadata
"""

import asyncio
import os
from pathlib import Path

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

from turbo.core.database.connection import get_db_session
from turbo.core.repositories import DocumentRepository, ProjectRepository
from turbo.core.schemas.document import DocumentCreate
from turbo.core.services import DocumentService

console = Console()


def determine_doc_type(file_path: Path) -> str:
    """Determine document type based on file path and name."""
    path_str = str(file_path).lower()
    name = file_path.stem.lower()

    # Architecture documents
    if "architecture" in path_str or "plan" in name:
        return "design"

    # Specifications
    if "specifications" in path_str or "spec" in name or "prd" in name:
        return "specification"

    # Requirements
    if "requirements" in name or "roadmap" in name:
        return "requirements"

    # API docs
    if "api" in name:
        return "api_doc"

    # README/guides
    if "readme" in name or "guide" in name or "reference" in name:
        return "user_guide"

    # Changelog
    if "changelog" in name or "history" in name:
        return "changelog"

    # Default
    return "other"


def extract_title_from_content(content: str, filename: str) -> str:
    """Extract title from markdown H1 or use filename."""
    lines = content.split("\n")
    for line in lines:
        if line.startswith("# "):
            return line[2:].strip()

    # Fallback to filename
    return filename.replace("_", " ").replace("-", " ").title()


async def migrate_docs():
    """Migrate all markdown files to Turbo Documents."""
    docs_dir = Path("/Users/alphonso/Documents/Code/PycharmProjects/turboCode/docs")

    if not docs_dir.exists():
        console.print("[red]Error: docs/ directory not found[/red]")
        return

    # Find all .md files
    md_files = list(docs_dir.rglob("*.md"))
    console.print(f"[cyan]Found {len(md_files)} markdown files to migrate[/cyan]\n")

    async for session in get_db_session():
        # Get Turbo Code project
        project_repo = ProjectRepository(session)
        projects = await project_repo.get_all()

        turbo_project = None
        for project in projects:
            if "turbo" in project.name.lower():
                turbo_project = project
                break

        if not turbo_project:
            console.print("[red]Error: Could not find Turbo Code project[/red]")
            return

        console.print(f"[green]Using project: {turbo_project.name} ({turbo_project.id})[/green]\n")

        # Create document service
        doc_repo = DocumentRepository(session)
        doc_service = DocumentService(doc_repo, project_repo)

        # Migrate each file
        results = []

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Migrating documents...", total=len(md_files))

            for md_file in md_files:
                try:
                    # Read file content
                    content = md_file.read_text(encoding="utf-8")

                    # Skip empty files
                    if not content.strip():
                        results.append((md_file.name, "skipped", "Empty file"))
                        progress.advance(task)
                        continue

                    # Determine metadata
                    doc_type = determine_doc_type(md_file)
                    title = extract_title_from_content(content, md_file.stem)

                    # Get relative path for version info
                    rel_path = md_file.relative_to(docs_dir)

                    # Create document
                    doc_data = DocumentCreate(
                        title=title,
                        content=content,
                        type=doc_type,
                        format="markdown",
                        version="1.0",
                        project_id=turbo_project.id,
                    )

                    doc = await doc_service.create_document(doc_data)
                    results.append((md_file.name, "success", f"{doc_type} - {doc.id}"))

                except Exception as e:
                    results.append((md_file.name, "error", str(e)))

                progress.advance(task)

        # Display results
        console.print("\n[bold]Migration Results:[/bold]\n")

        table = Table(show_header=True)
        table.add_column("File", style="cyan")
        table.add_column("Status", style="white")
        table.add_column("Details", style="dim")

        success_count = 0
        error_count = 0
        skip_count = 0

        for filename, status, details in results:
            if status == "success":
                table.add_row(filename, "[green]✓ Migrated[/green]", details)
                success_count += 1
            elif status == "error":
                table.add_row(filename, "[red]✗ Error[/red]", details)
                error_count += 1
            else:
                table.add_row(filename, "[yellow]⊘ Skipped[/yellow]", details)
                skip_count += 1

        console.print(table)

        # Summary
        console.print(f"\n[bold]Summary:[/bold]")
        console.print(f"  [green]✓ Migrated: {success_count}[/green]")
        console.print(f"  [yellow]⊘ Skipped: {skip_count}[/yellow]")
        console.print(f"  [red]✗ Errors: {error_count}[/red]")
        console.print(f"\n[dim]Documents are now stored in the database and can be viewed at:")
        console.print(f"http://localhost:3001/documents[/dim]")


if __name__ == "__main__":
    asyncio.run(migrate_docs())