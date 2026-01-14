"""Tag CLI commands."""


import click
from rich import box
from rich.console import Console
from rich.table import Table

from turbo.cli.utils import create_tag_service, handle_exceptions, run_async
from turbo.core.database import get_db_session
from turbo.core.schemas import TagCreate, TagUpdate
from turbo.utils.exceptions import TagNotFoundError, ValidationError

console = Console()

# Valid choices for CLI options
COLOR_CHOICES = [
    "red",
    "blue",
    "green",
    "yellow",
    "purple",
    "orange",
    "pink",
    "gray",
    "black",
    "white",
]
FORMAT_CHOICES = ["table", "json", "csv"]

# Color name to hex mapping
COLOR_HEX_MAP = {
    "red": "#FF0000",
    "blue": "#0000FF",
    "green": "#00FF00",
    "yellow": "#FFFF00",
    "purple": "#800080",
    "orange": "#FFA500",
    "pink": "#FFC0CB",
    "gray": "#808080",
    "black": "#000000",
    "white": "#FFFFFF",
}

# Reverse mapping for display
HEX_COLOR_MAP = {v: k for k, v in COLOR_HEX_MAP.items()}


def _get_color_name(hex_color: str) -> str:
    """Convert hex color to display name."""
    return HEX_COLOR_MAP.get(hex_color, hex_color)


@click.group()
def tags_group():
    """Manage tags."""
    pass


@tags_group.command()
@click.option("--name", required=True, help="Tag name")
@click.option("--description", help="Tag description")
@click.option(
    "--color", type=click.Choice(COLOR_CHOICES), default="blue", help="Tag color"
)
@handle_exceptions
def create(name, description, color):
    """Create a new tag."""

    async def _create():
        async for session in get_db_session():
            service = create_tag_service(session)

            tag_data = TagCreate(
                name=name,
                description=description,
                color=COLOR_HEX_MAP.get(color, color),  # Convert color name to hex
            )

            tag = await service.create_tag(tag_data)

            console.print("[green]✓[/green] Tag created successfully!")
            console.print(f"  ID: {tag.id}")
            color_name = _get_color_name(tag.color)
            console.print(f"  Name: [{color_name}]{tag.name}[/{color_name}]")
            if tag.description:
                console.print(f"  Description: {tag.description}")

            return tag

    run_async(_create())


@tags_group.command()
@click.option("--color", type=click.Choice(COLOR_CHOICES), help="Filter by color")
@click.option(
    "--format", type=click.Choice(FORMAT_CHOICES), default="table", help="Output format"
)
@click.option("--limit", type=int, help="Limit number of results")
@click.option("--offset", type=int, help="Offset for pagination")
@handle_exceptions
def list(color, format, limit, offset):
    """List all tags."""

    async def _list():
        async for session in get_db_session():
            service = create_tag_service(session)

            if color:
                hex_color = COLOR_HEX_MAP.get(color, color)
                tags = await service.get_tags_by_color(hex_color)
            else:
                tags = await service.get_all_tags(limit=limit, offset=offset)

            if not tags:
                console.print("[yellow]No tags found[/yellow]")
                return

            if format == "table":
                _display_tags_table(tags)
            elif format == "json":
                import json

                console.print(
                    json.dumps([t.model_dump() for t in tags], indent=2, default=str)
                )
            elif format == "csv":
                _display_tags_csv(tags)

    run_async(_list())


@tags_group.command()
@click.argument("tag_id", type=click.UUID)
@click.option("--detailed", is_flag=True, help="Show detailed information")
@handle_exceptions
def get(tag_id, detailed):
    """Get tag by ID."""

    async def _get():
        async for session in get_db_session():
            service = create_tag_service(session)

            try:
                tag = await service.get_tag_by_id(tag_id)

                if detailed:
                    _display_tag_detailed(tag)
                else:
                    _display_tag_summary(tag)

            except TagNotFoundError:
                console.print(f"[red]Tag with ID {tag_id} not found[/red]")
                return

    run_async(_get())


@tags_group.command()
@click.argument("tag_id", type=click.UUID)
@click.option("--name", help="Update tag name")
@click.option("--description", help="Update tag description")
@click.option("--color", type=click.Choice(COLOR_CHOICES), help="Update tag color")
@handle_exceptions
def update(tag_id, name, description, color):
    """Update a tag."""

    async def _update():
        async for session in get_db_session():
            service = create_tag_service(session)

            # Build update data from provided options
            update_data = {}
            if name:
                update_data["name"] = name
            if description is not None:  # Allow empty string
                update_data["description"] = description
            if color:
                update_data["color"] = COLOR_HEX_MAP.get(
                    color, color
                )  # Convert color name to hex

            if not update_data:
                console.print("[yellow]No updates provided[/yellow]")
                return

            try:
                tag_update = TagUpdate(**update_data)
                tag = await service.update_tag(tag_id, tag_update)

                console.print("[green]✓[/green] Tag updated successfully!")
                _display_tag_summary(tag)

            except TagNotFoundError:
                console.print(f"[red]Tag with ID {tag_id} not found[/red]")
            except ValidationError as e:
                console.print(f"[red]Validation error: {e}[/red]")

    run_async(_update())


@tags_group.command()
@click.argument("tag_id", type=click.UUID)
@click.option("--confirm", is_flag=True, help="Skip confirmation prompt")
@handle_exceptions
def delete(tag_id, confirm):
    """Delete a tag."""
    if not confirm:
        if not click.confirm("Are you sure you want to delete this tag?"):
            console.print("[yellow]Operation cancelled[/yellow]")
            return

    async def _delete():
        async for session in get_db_session():
            service = create_tag_service(session)

            try:
                await service.delete_tag(tag_id)
                console.print("[green]✓[/green] Tag deleted successfully!")

            except TagNotFoundError:
                console.print(f"[red]Tag with ID {tag_id} not found[/red]")

    run_async(_delete())


@tags_group.command()
@click.argument("query")
@click.option(
    "--format", type=click.Choice(FORMAT_CHOICES), default="table", help="Output format"
)
@handle_exceptions
def search(query, format):
    """Search tags by name."""

    async def _search():
        async for session in get_db_session():
            service = create_tag_service(session)

            tags = await service.search_tags_by_name(query)

            if not tags:
                console.print(f"[yellow]No tags found matching '{query}'[/yellow]")
                return

            console.print(f"[blue]Found {len(tags)} tag(s) matching '{query}':[/blue]")

            if format == "table":
                _display_tags_table(tags)
            elif format == "json":
                import json

                console.print(
                    json.dumps([t.model_dump() for t in tags], indent=2, default=str)
                )

    run_async(_search())


@tags_group.command()
@click.option(
    "--format", type=click.Choice(FORMAT_CHOICES), default="table", help="Output format"
)
@handle_exceptions
def usage(format):
    """Show tag usage statistics."""

    async def _usage():
        async for session in get_db_session():
            service = create_tag_service(session)

            stats = await service.get_tag_usage_statistics()

            if not stats:
                console.print("[yellow]No tag usage data available[/yellow]")
                return

            console.print("[blue]Tag Usage Statistics:[/blue]")

            if format == "table":
                table = Table(box=box.SIMPLE_HEAD)
                table.add_column("Tag", style="bold")
                table.add_column("Color", style="cyan")
                table.add_column("Projects", style="green")
                table.add_column("Issues", style="yellow")
                table.add_column("Documents", style="magenta")
                table.add_column("Total Usage", style="red")

                for stat in stats:
                    tag_name = f"[{stat.get('color', 'white')}]{stat.get('name', 'Unknown')}[/{stat.get('color', 'white')}]"
                    table.add_row(
                        tag_name,
                        stat.get("color", "Unknown"),
                        str(stat.get("project_count", 0)),
                        str(stat.get("issue_count", 0)),
                        str(stat.get("document_count", 0)),
                        str(stat.get("total_usage", 0)),
                    )

                console.print(table)

            elif format == "json":
                import json

                console.print(json.dumps(stats, indent=2, default=str))

            elif format == "csv":
                console.print("Tag,Color,Projects,Issues,Documents,Total")
                for stat in stats:
                    console.print(
                        f"{stat.get('name', 'Unknown')},{stat.get('color', 'Unknown')},{stat.get('project_count', 0)},{stat.get('issue_count', 0)},{stat.get('document_count', 0)},{stat.get('total_usage', 0)}"
                    )

    run_async(_usage())


@tags_group.command()
@handle_exceptions
def colors():
    """Show available tag colors with examples."""
    console.print("[bold]Available Tag Colors:[/bold]\n")

    table = Table(box=box.SIMPLE)
    table.add_column("Color", style="cyan")
    table.add_column("Example", style="white")
    table.add_column("Usage", style="dim")

    color_examples = {
        "red": ("Critical, Urgent, Bug", "High priority items"),
        "orange": ("Warning, Review", "Items needing attention"),
        "yellow": ("In Progress, Pending", "Active work items"),
        "green": ("Complete, Success", "Finished or successful items"),
        "blue": ("Info, Documentation", "Informational content"),
        "purple": ("Feature, Enhancement", "New functionality"),
        "pink": ("Design, UI/UX", "Design-related items"),
        "gray": ("Archive, Deprecated", "Inactive or old items"),
        "black": ("Internal, System", "Internal system items"),
        "white": ("Default, General", "General purpose tags"),
    }

    for color, (example, usage) in color_examples.items():
        colored_example = f"[{color}]{example}[/{color}]"
        table.add_row(color.capitalize(), colored_example, usage)

    console.print(table)

    console.print(
        '\n[dim]Use: turbo tags create --name "tag-name" --color <color>[/dim]'
    )


@tags_group.command()
@click.argument("tag_id", type=click.UUID)
@handle_exceptions
def related(tag_id):
    """Show items related to a tag."""

    async def _related():
        async for session in get_db_session():
            service = create_tag_service(session)

            try:
                # Get the tag
                tag = await service.get_tag_by_id(tag_id)

                console.print(
                    f"[bold]Items tagged with [{tag.color}]{tag.name}[/{tag.color}]:[/bold]\n"
                )

                # Get related items
                related_items = await service.get_tag_related_items(tag_id)

                # Display projects
                if related_items.get("projects"):
                    console.print("[cyan]Projects:[/cyan]")
                    for project in related_items["projects"]:
                        console.print(f"  • {project.name} ({project.id})")
                    console.print()

                # Display issues
                if related_items.get("issues"):
                    console.print("[yellow]Issues:[/yellow]")
                    for issue in related_items["issues"]:
                        console.print(f"  • {issue.title} ({issue.id})")
                    console.print()

                # Display documents
                if related_items.get("documents"):
                    console.print("[magenta]Documents:[/magenta]")
                    for document in related_items["documents"]:
                        console.print(f"  • {document.title} ({document.id})")
                    console.print()

                if not any(related_items.values()):
                    console.print(
                        "[dim]No items are currently tagged with this tag.[/dim]"
                    )

            except TagNotFoundError:
                console.print(f"[red]Tag with ID {tag_id} not found[/red]")

    run_async(_related())


def _display_tags_table(tags):
    """Display tags in table format."""
    table = Table(box=box.SIMPLE_HEAD)
    table.add_column("ID", style="dim")
    table.add_column("Name", style="bold")
    table.add_column("Color", style="cyan")
    table.add_column("Description", style="white")
    table.add_column("Created", style="dim")

    for tag in tags:
        created = (
            tag.created_at.strftime("%Y-%m-%d")
            if hasattr(tag.created_at, "strftime")
            else str(tag.created_at)[:10]
        )
        color_name = _get_color_name(tag.color)
        colored_name = f"[{color_name}]{tag.name}[/{color_name}]"
        description = (
            tag.description[:50] + "..."
            if tag.description and len(tag.description) > 50
            else (tag.description or "")
        )

        table.add_row(
            str(tag.id)[:8] + "...", colored_name, color_name, description, created
        )

    console.print(table)


def _display_tags_csv(tags):
    """Display tags in CSV format."""
    console.print("ID,Name,Color,Description,Created")
    for tag in tags:
        created = (
            tag.created_at.strftime("%Y-%m-%d")
            if hasattr(tag.created_at, "strftime")
            else str(tag.created_at)[:10]
        )
        name = tag.name.replace(",", ";")  # Replace commas to avoid CSV issues
        description = (tag.description or "").replace(",", ";")
        color_name = _get_color_name(tag.color)
        console.print(f"{tag.id},{name},{color_name},{description},{created}")


def _display_tag_summary(tag):
    """Display tag summary."""
    color_name = _get_color_name(tag.color)
    colored_name = f"[{color_name}]{tag.name}[/{color_name}]"
    console.print(f"[bold]{colored_name}[/bold]")
    console.print(f"  ID: {tag.id}")
    console.print(f"  Color: [{color_name}]{color_name}[/{color_name}]")
    if tag.description:
        console.print(f"  Description: {tag.description}")


def _display_tag_detailed(tag):
    """Display detailed tag information."""
    table = Table(box=box.SIMPLE)
    table.add_column("Field", style="cyan")
    table.add_column("Value", style="white")

    table.add_row("ID", str(tag.id))
    table.add_row("Name", tag.name)
    color_name = _get_color_name(tag.color)
    table.add_row("Color", f"[{color_name}]{color_name}[/{color_name}]")
    table.add_row("Description", tag.description or "None")

    created = (
        tag.created_at.strftime("%Y-%m-%d %H:%M:%S")
        if hasattr(tag.created_at, "strftime")
        else str(tag.created_at)
    )
    updated = (
        tag.updated_at.strftime("%Y-%m-%d %H:%M:%S")
        if hasattr(tag.updated_at, "strftime")
        else str(tag.updated_at)
    )

    table.add_row("Created", created)
    table.add_row("Updated", updated)

    console.print(table)
