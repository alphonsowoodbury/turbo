#!/usr/bin/env python3
"""Test semantic search on the knowledge graph."""

import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from turbo.core.services.graph import GraphService
from turbo.core.schemas.graph import GraphSearchQuery


console = Console()


async def test_search(query_text: str, limit: int = 5):
    """Test semantic search with a query."""
    console.print(f"\n[bold cyan]Query:[/bold cyan] {query_text}")

    graph = GraphService()

    query = GraphSearchQuery(
        query=query_text,
        limit=limit,
        min_relevance=0.3  # Lower threshold to see more results
    )

    results = await graph.search(query)

    # Create results table
    table = Table(title=f"Found {results.total_results} results in {results.execution_time_ms:.1f}ms")
    table.add_column("Score", style="cyan", width=6)
    table.add_column("Type", style="magenta", width=12)
    table.add_column("Title", style="green")

    for result in results.results:
        # Extract title from metadata or content
        title = result.metadata.get("title", "No title")
        if len(title) > 60:
            title = title[:57] + "..."

        table.add_row(
            f"{result.relevance_score:.3f}",
            result.metadata.get("type", "unknown"),
            title
        )

    console.print(table)

    # Show top result details
    if results.results:
        top = results.results[0]
        title = top.metadata.get("title", "No title")
        content_preview = top.content[:200] + "..." if len(top.content) > 200 else top.content

        panel = Panel(
            f"[bold]{title}[/bold]\n\n{content_preview}",
            title=f"Top Result ({top.relevance_score:.3f} relevance)",
            border_style="green"
        )
        console.print(panel)

    await graph.close()


async def main():
    """Run semantic search tests."""
    console.print(Panel.fit(
        "[bold]🚀 Knowledge Graph Semantic Search Demo[/bold]\n"
        "Testing how well the graph understands meaning vs keywords",
        border_style="blue"
    ))

    # Test queries that showcase semantic understanding
    test_queries = [
        "authentication and user login",
        "organizing and managing work",
        "AI features and intelligent tools",
        "visual design and user interface",
        "code quality and development tools",
    ]

    for query in test_queries:
        await test_search(query, limit=5)
        await asyncio.sleep(0.5)  # Small delay for readability

    console.print("\n[bold green]✓ Demo complete![/bold green]")
    console.print("\n[dim]The graph understands semantic meaning, not just keywords![/dim]")
    console.print("[dim]Try your own queries with: [cyan]turbo search \"your query here\"[/cyan] (when we add the CLI command)[/dim]")


if __name__ == "__main__":
    asyncio.run(main())