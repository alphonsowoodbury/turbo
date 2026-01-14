"""CLI commands for agent management."""

import click
from rich.console import Console
from rich.table import Table

from turbo.cli.utils import handle_exceptions, run_async
from turbo.core.database.connection import get_db_session
from turbo.core.services.agents import PMAgent

console = Console()


@click.group()
def agents_group():
    """Manage autonomous agents."""
    pass


@agents_group.command("run-pm")
@click.option(
    "--user",
    "-u",
    default="@alphonso",
    help="User to mention in comments",
)
@click.option(
    "--dry-run",
    "-d",
    is_flag=True,
    help="Show what would be done without making changes",
)
@handle_exceptions
def run_pm_agent(user, dry_run):
    """
    Run the Project Management Agent to audit and organize issues.

    The PM Agent will:
    \b
    - Audit all open issues
    - Close issues that appear complete
    - Request user confirmation for uncertain cases
    - Suggest organization (initiatives/milestones)
    - Add comments documenting all findings
    """
    console.print("\n🤖 [bold cyan]PM Agent Starting...[/bold cyan]\n")

    if dry_run:
        console.print("⚠️  [yellow]DRY RUN MODE - No changes will be made[/yellow]\n")

    async def run_agent():
        async for session in get_db_session():
            agent = PMAgent(session, user_mention=user)

            if dry_run:
                console.print("📊 Would audit issues and add comments (dry run)")
                return

            with console.status("[bold green]Auditing issues..."):
                result = await agent.run_audit()

            # Display results
            console.print("\n✅ [bold green]PM Agent Completed![/bold green]\n")

            table = Table(title="Audit Summary")
            table.add_column("Metric", style="cyan")
            table.add_column("Count", style="magenta")

            table.add_row("Issues Audited", str(result["issues_audited"]))
            table.add_row("Issues Closed", str(result["issues_closed"]))
            table.add_row("Issues Updated", str(result["issues_updated"]))
            table.add_row("Comments Added", str(result["comments_added"]))
            table.add_row("Decisions Needed", str(result["decisions_needed"]))

            console.print(table)

            if result["decisions_needed"] > 0:
                console.print(
                    f"\n💬 [yellow]{result['decisions_needed']} issues need your input.[/yellow]"
                )
                console.print("   Check issue comments for agent questions.\n")

    run_async(run_agent())


@agents_group.command("list")
@handle_exceptions
def list_agents():
    """List all configured agents."""
    console.print("\n🤖 [bold cyan]Available Agents[/bold cyan]\n")

    table = Table()
    table.add_column("Agent", style="cyan")
    table.add_column("Type", style="magenta")
    table.add_column("Status", style="green")
    table.add_column("Description")

    table.add_row(
        "PM Agent",
        "Project Management",
        "✅ Ready",
        "Audits issues, closes completed work, organizes backlog",
    )
    table.add_row(
        "Research Agent",
        "Knowledge Gathering",
        "🚧 Coming Soon",
        "Monitors literature feeds, summarizes findings",
    )
    table.add_row(
        "Codebase Agent",
        "Code Understanding",
        "🚧 Coming Soon",
        "Indexes codebase, answers architecture questions",
    )
    table.add_row(
        "Workflow Agent",
        "Automation",
        "🚧 Coming Soon",
        "Executes custom workflows and automations",
    )

    console.print(table)
    console.print("\n💡 [dim]Run 'turbo agents run-pm' to start the PM Agent[/dim]\n")
