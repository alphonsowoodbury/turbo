#!/usr/bin/env python3
"""Script to ingest existing issues into the knowledge graph."""

import asyncio
import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn

from turbo.core.database.connection import get_db_session
from turbo.core.repositories.issue import IssueRepository
from turbo.core.services.graph import GraphService
from turbo.core.schemas.graph import GraphNodeCreate
from turbo.utils.config import get_settings


console = Console()


async def ingest_issues():
    """Ingest all issues into the knowledge graph."""
    console.print("[bold blue]Starting issue ingestion to knowledge graph...[/bold blue]\n")

    # Check if graph is enabled
    settings = get_settings()
    if not settings.graph.enabled:
        console.print("[yellow]Knowledge graph is disabled in settings. Enable it to continue.[/yellow]")
        return

    console.print(f"[cyan]Using local embedding model: {settings.graph.embedding_model}[/cyan]")
    console.print("[dim]First run will download ~90MB model, then it's cached locally[/dim]\n")

    # Initialize graph service
    graph_service = GraphService()

    # Test connection
    console.print("Testing Neo4j connection...")
    health = await graph_service.health_check()
    if health["status"] != "healthy":
        console.print(f"[red]Neo4j connection failed: {health.get('error', 'Unknown error')}[/red]")
        console.print(f"URI: {settings.graph.uri}")
        console.print("Make sure Neo4j is running (docker-compose up neo4j)")
        return

    console.print("[green]✓[/green] Neo4j connection successful\n")

    # Get all issues from database
    async for session in get_db_session():
        issue_repo = IssueRepository(session)
        console.print("Fetching issues from database...")
        issues = await issue_repo.get_all()
        console.print(f"[green]✓[/green] Found {len(issues)} issues\n")

        if not issues:
            console.print("[yellow]No issues found to ingest.[/yellow]")
            await graph_service.close()
            return

        # Ingest issues with progress bar
        success_count = 0
        error_count = 0

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            console=console,
        ) as progress:
            task = progress.add_task(
                f"Ingesting {len(issues)} issues...", total=len(issues)
            )

            for issue in issues:
                try:
                    # Build content string from issue
                    content = f"""
Title: {issue.title}

Description:
{issue.description}

Type: {issue.type}
Status: {issue.status}
Priority: {issue.priority}
""".strip()

                    if issue.assignee:
                        content += f"\nAssignee: {issue.assignee}"

                    # Create node data
                    node_data = GraphNodeCreate(
                        entity_id=issue.id,
                        entity_type="issue",
                        content=content,
                        metadata={
                            "title": issue.title,
                            "type": issue.type,
                            "status": issue.status,
                            "priority": issue.priority,
                            "project_id": str(issue.project_id) if issue.project_id else None,
                        },
                    )

                    # Add to graph
                    await graph_service.add_episode(node_data)
                    success_count += 1

                except Exception as e:
                    console.print(f"\n[red]Error ingesting issue {issue.id}: {e}[/red]")
                    error_count += 1

                progress.update(task, advance=1)

        console.print(f"\n[bold green]Ingestion complete![/bold green]")
        console.print(f"  ✓ Successfully ingested: {success_count} issues")
        if error_count > 0:
            console.print(f"  ✗ Errors: {error_count} issues")

        # Get graph statistics
        console.print("\n[bold]Knowledge Graph Statistics:[/bold]")
        try:
            stats = await graph_service.get_statistics()
            console.print(f"  Total nodes: {stats.total_nodes}")
            console.print(f"  Total edges: {stats.total_edges}")
            if stats.entities_by_type:
                console.print("  Entities by type:")
                for entity_type, count in stats.entities_by_type.items():
                    console.print(f"    - {entity_type}: {count}")
        except Exception as e:
            console.print(f"[yellow]Could not retrieve stats: {e}[/yellow]")

        # Close connection
        await graph_service.close()
        console.print("\n[green]✓[/green] Done!")


if __name__ == "__main__":
    asyncio.run(ingest_issues())
