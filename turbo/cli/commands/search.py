"""Global search command."""

from typing import Any

import click
from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from turbo.api.dependencies import (
    get_document_service,
    get_issue_service,
    get_project_service,
    get_tag_service,
)
from turbo.cli.utils import handle_exceptions, run_async
from turbo.core.database import get_db_session
from turbo.core.schemas.graph import GraphSearchQuery
from turbo.core.services.graph import GraphService
from turbo.utils.config import get_settings

console = Console()

# Valid choices for CLI options
TYPE_CHOICES = ["all", "projects", "issues", "documents", "tags"]
FORMAT_CHOICES = ["table", "json"]


@click.command()
@click.argument("query")
@click.option(
    "--type",
    type=click.Choice(TYPE_CHOICES),
    default="all",
    help="Search in specific entity type",
)
@click.option(
    "--format", type=click.Choice(FORMAT_CHOICES), default="table", help="Output format"
)
@click.option("--limit", type=int, default=20, help="Limit number of results")
@click.option(
    "--semantic",
    is_flag=True,
    help="Use semantic search (knowledge graph) - understands meaning, not just keywords",
)
@click.option(
    "--min-relevance",
    type=float,
    default=0.5,
    help="Minimum relevance score for semantic search (0.0-1.0)",
)
@handle_exceptions
def search_command(query, type, format, limit, semantic, min_relevance):
    """
    Search across all entities in the workspace.

    Two search modes:

    \b
    1. Keyword search (default): Fast exact/partial text matching
       Example: turbo search "authentication"

    \b
    2. Semantic search (--semantic): AI-powered meaning-based search
       Example: turbo search "user login problems" --semantic

    \b
    Semantic search understands concepts and finds related items even if
    they use different words. It's powered by local embeddings - no API
    keys needed, completely private, and free forever.
    """

    async def _search():
        # Check if semantic search is requested
        if semantic:
            await _semantic_search(query, type, format, limit, min_relevance)
        else:
            await _keyword_search(query, type, format, limit)

    run_async(_search())


async def _semantic_search(query: str, entity_type: str, output_format: str, limit: int, min_relevance: float):
    """Perform semantic search using the knowledge graph."""
    settings = get_settings()

    if not settings.graph.enabled:
        console.print("[yellow]Knowledge graph is disabled in settings.[/yellow]")
        console.print("[dim]Run 'turbo config' to enable it, or use keyword search without --semantic flag[/dim]")
        return

    # Show that we're using semantic search
    console.print(Panel.fit(
        f"[bold cyan]Semantic Search:[/bold cyan] {query}\n"
        f"[dim]Understanding meaning, not just keywords...[/dim]",
        border_style="cyan"
    ))

    graph_service = GraphService()

    try:
        # Check Neo4j connection
        health = await graph_service.health_check()
        if health["status"] != "healthy":
            console.print("[red]Neo4j is not available. Make sure it's running:[/red]")
            console.print("[dim]docker-compose up -d neo4j[/dim]\n")
            return

        # Build entity type filter
        entity_types = None
        if entity_type != "all":
            # Map CLI type to graph entity types
            type_map = {
                "projects": ["project"],
                "issues": ["issue"],
                "documents": ["document"],
                "tags": ["tag"],
            }
            entity_types = type_map.get(entity_type)

        # Perform semantic search
        search_query = GraphSearchQuery(
            query=query,
            limit=limit,
            entity_types=entity_types,
            min_relevance=min_relevance,
        )

        results = await graph_service.search(search_query)

        # Display results
        if output_format == "table":
            _display_semantic_results_table(results)
        else:
            _display_semantic_results_json(results)

    except Exception as e:
        console.print(f"[red]Semantic search failed: {e}[/red]")
        console.print("[dim]Try keyword search without --semantic flag[/dim]")
    finally:
        await graph_service.close()


async def _keyword_search(query: str, entity_type: str, output_format: str, limit: int):
    """Perform traditional keyword search."""
    async for session in get_db_session():
        project_service = get_project_service(session)
        issue_service = get_issue_service(session)
        document_service = get_document_service(session)
        tag_service = get_tag_service(session)

        results = {}

        try:
            if entity_type in ["all", "projects"]:
                results["projects"] = await project_service.search_projects_by_name(
                    query
                )

            if entity_type in ["all", "issues"]:
                results["issues"] = await issue_service.search_issues_by_title(
                    query
                )

            if entity_type in ["all", "documents"]:
                results["documents"] = await document_service.search_documents(
                    query
                )

            if entity_type in ["all", "tags"]:
                results["tags"] = await tag_service.search_tags_by_name(query)

            # Display results
            if output_format == "table":
                _display_search_results_table(results, query, limit)
            else:
                _display_search_results_json(results, query, limit)

        except Exception as e:
            console.print(f"[red]Search failed: {e}[/red]")


def _display_search_results_table(
    results: dict[str, list[Any]], query: str, limit: int
):
    """Display search results in table format."""
    total_results = sum(len(items) for items in results.values())

    if total_results == 0:
        console.print(f"[yellow]No results found for '{query}'[/yellow]")
        return

    console.print(f"[blue]Found {total_results} result(s) for '{query}':[/blue]\n")

    shown_count = 0

    # Display projects
    if results.get("projects"):
        console.print("[bold cyan]Projects:[/bold cyan]")
        table = Table(box=box.SIMPLE)
        table.add_column("ID", style="dim")
        table.add_column("Name", style="bold")
        table.add_column("Status", style="cyan")
        table.add_column("Priority", style="yellow")

        for project in results["projects"][: limit - shown_count]:
            table.add_row(
                str(project.id)[:8] + "...",
                project.name,
                project.status,
                project.priority,
            )
            shown_count += 1

        console.print(table)
        console.print()

    # Display issues
    if "issues" in results and results["issues"] and shown_count < limit:
        console.print("[bold cyan]Issues:[/bold cyan]")
        table = Table(box=box.SIMPLE)
        table.add_column("ID", style="dim")
        table.add_column("Title", style="bold")
        table.add_column("Status", style="cyan")
        table.add_column("Priority", style="yellow")

        for issue in results["issues"][: limit - shown_count]:
            table.add_row(
                str(issue.id)[:8] + "...",
                issue.title[:50] + "..." if len(issue.title) > 50 else issue.title,
                issue.status,
                issue.priority,
            )
            shown_count += 1

        console.print(table)
        console.print()

    # Display documents
    if "documents" in results and results["documents"] and shown_count < limit:
        console.print("[bold cyan]Documents:[/bold cyan]")
        table = Table(box=box.SIMPLE)
        table.add_column("ID", style="dim")
        table.add_column("Title", style="bold")
        table.add_column("Type", style="cyan")
        table.add_column("Size", style="green")

        for document in results["documents"][: limit - shown_count]:
            content_size = len(document.content or "")
            size_str = (
                f"{content_size} chars"
                if content_size < 1000
                else f"{content_size/1000:.1f}K"
            )

            table.add_row(
                str(document.id)[:8] + "...",
                (
                    document.title[:50] + "..."
                    if len(document.title) > 50
                    else document.title
                ),
                document.document_type,
                size_str,
            )
            shown_count += 1

        console.print(table)
        console.print()

    # Display tags
    if "tags" in results and results["tags"] and shown_count < limit:
        console.print("[bold cyan]Tags:[/bold cyan]")
        table = Table(box=box.SIMPLE)
        table.add_column("ID", style="dim")
        table.add_column("Name", style="bold")
        table.add_column("Color", style="cyan")
        table.add_column("Description", style="white")

        for tag in results["tags"][: limit - shown_count]:
            colored_name = f"[{tag.color}]{tag.name}[/{tag.color}]"
            description = (
                tag.description[:40] + "..."
                if tag.description and len(tag.description) > 40
                else (tag.description or "")
            )

            table.add_row(str(tag.id)[:8] + "...", colored_name, tag.color, description)
            shown_count += 1

        console.print(table)

    if shown_count >= limit and total_results > limit:
        console.print(
            f"[dim]... and {total_results - limit} more results (use --limit to see more)[/dim]"
        )


def _display_search_results_json(results: dict[str, list[Any]], query: str, limit: int):
    """Display search results in JSON format."""
    import json

    output = {
        "query": query,
        "total_results": sum(len(items) for items in results.values()),
        "results": {},
    }

    for entity_type, items in results.items():
        if items:
            output["results"][entity_type] = [
                item.model_dump() for item in items[:limit]
            ]

    console.print(json.dumps(output, indent=2, default=str))


def _display_semantic_results_table(results):
    """Display semantic search results in table format."""
    from turbo.core.schemas.graph import GraphSearchResponse

    if not isinstance(results, GraphSearchResponse):
        console.print("[red]Invalid search results[/red]")
        return

    if results.total_results == 0:
        console.print(f"[yellow]No results found for '{results.query}'[/yellow]")
        console.print("[dim]Try lowering --min-relevance threshold or different search terms[/dim]")
        return

    # Create results table
    table = Table(
        title=f"Found {results.total_results} result(s) in {results.execution_time_ms:.0f}ms",
        box=box.ROUNDED
    )
    table.add_column("Relevance", style="cyan", width=8, justify="right")
    table.add_column("Type", style="magenta", width=10)
    table.add_column("Title", style="green")
    table.add_column("ID", style="dim", width=10)

    for result in results.results:
        # Extract title from metadata or content preview
        title = result.metadata.get("title", "No title")
        if not title or title == "No title":
            # Use content preview if no title
            title = result.content[:60] + "..." if len(result.content) > 60 else result.content

        # Truncate long titles
        if len(title) > 60:
            title = title[:57] + "..."

        # Format relevance score
        relevance = f"{result.relevance_score:.3f}"

        # Color code relevance
        if result.relevance_score >= 0.8:
            relevance = f"[bold green]{relevance}[/bold green]"
        elif result.relevance_score >= 0.6:
            relevance = f"[green]{relevance}[/green]"
        elif result.relevance_score >= 0.4:
            relevance = f"[yellow]{relevance}[/yellow]"
        else:
            relevance = f"[dim]{relevance}[/dim]"

        table.add_row(
            relevance,
            result.entity_type,
            title,
            str(result.entity_id)[:8] + "..."
        )

    console.print(table)

    # Show top result details
    if results.results:
        top = results.results[0]
        title = top.metadata.get("title", "No title")
        content_preview = top.content[:200] + "..." if len(top.content) > 200 else top.content

        # Extract additional metadata
        metadata_lines = []
        if "status" in top.metadata:
            metadata_lines.append(f"Status: {top.metadata['status']}")
        if "priority" in top.metadata:
            metadata_lines.append(f"Priority: {top.metadata['priority']}")
        if "type" in top.metadata:
            metadata_lines.append(f"Type: {top.metadata['type']}")

        metadata_str = " | ".join(metadata_lines) if metadata_lines else ""

        panel_content = f"[bold]{title}[/bold]"
        if metadata_str:
            panel_content += f"\n[dim]{metadata_str}[/dim]"
        panel_content += f"\n\n{content_preview}"

        panel = Panel(
            panel_content,
            title=f"Top Result ({top.relevance_score:.3f} relevance)",
            border_style="green"
        )
        console.print()
        console.print(panel)


def _display_semantic_results_json(results):
    """Display semantic search results in JSON format."""
    import json
    from turbo.core.schemas.graph import GraphSearchResponse

    if not isinstance(results, GraphSearchResponse):
        console.print("[red]Invalid search results[/red]")
        return

    output = {
        "query": results.query,
        "total_results": results.total_results,
        "execution_time_ms": results.execution_time_ms,
        "results": []
    }

    for result in results.results:
        output["results"].append({
            "entity_id": str(result.entity_id),
            "entity_type": result.entity_type,
            "relevance_score": result.relevance_score,
            "content": result.content,
            "metadata": result.metadata,
            "created_at": result.created_at.isoformat() if result.created_at else None,
        })

    console.print(json.dumps(output, indent=2))
