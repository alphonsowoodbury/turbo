"""CLI utility functions."""

import asyncio
import logging
import sys

from rich.console import Console

from turbo.core.repositories import (
    DocumentRepository,
    IssueRepository,
    IssueDependencyRepository,
    MilestoneRepository,
    ProjectRepository,
    TagRepository,
)
from turbo.core.services import (
    DocumentService,
    IssueService,
    ProjectService,
    TagService,
)

console = Console()


def run_async(coro):
    """Helper to run async functions in Click commands."""
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    return loop.run_until_complete(coro)


def handle_exceptions(func):
    """Decorator to handle common exceptions in CLI commands."""
    import functools

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except KeyboardInterrupt:
            console.print("\n[yellow]Operation cancelled by user[/yellow]")
            sys.exit(1)
        except Exception as e:
            if logging.getLogger().level == logging.DEBUG:
                console.print_exception()
            else:
                console.print(f"[red]Error: {e!s}[/red]")
            sys.exit(1)

    return wrapper


def create_project_service(session) -> ProjectService:
    """Create project service with repositories."""
    project_repo = ProjectRepository(session)
    issue_repo = IssueRepository(session)
    document_repo = DocumentRepository(session)
    return ProjectService(project_repo, issue_repo, document_repo)


def create_issue_service(session) -> IssueService:
    """Create issue service with repositories."""
    issue_repo = IssueRepository(session)
    project_repo = ProjectRepository(session)
    milestone_repo = MilestoneRepository(session)
    dependency_repo = IssueDependencyRepository(session)
    return IssueService(issue_repo, project_repo, milestone_repo, dependency_repo)


def create_document_service(session) -> DocumentService:
    """Create document service with repositories."""
    document_repo = DocumentRepository(session)
    project_repo = ProjectRepository(session)
    return DocumentService(document_repo, project_repo)


def create_tag_service(session) -> TagService:
    """Create tag service with repositories."""
    tag_repo = TagRepository(session)
    return TagService(tag_repo)
