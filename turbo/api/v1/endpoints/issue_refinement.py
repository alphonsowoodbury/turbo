"""Issue Refinement API endpoints."""

from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from turbo.api.dependencies import get_db_session
from turbo.core.repositories.issue import IssueRepository
from turbo.core.repositories.issue_dependency import IssueDependencyRepository
from turbo.core.repositories.project import ProjectRepository
from turbo.core.repositories.tag import TagRepository
from turbo.core.services.issue_refinement import IssueRefinementService

router = APIRouter(prefix="/issue-refinement", tags=["issue-refinement"])


def get_refinement_service(
    session: AsyncSession = Depends(get_db_session),
) -> IssueRefinementService:
    """Get issue refinement service dependency."""
    return IssueRefinementService(
        session=session,
        issue_repo=IssueRepository(session),
        dependency_repo=IssueDependencyRepository(session),
        project_repo=ProjectRepository(session),
        tag_repo=TagRepository(session),
    )


@router.post("/analyze")
async def analyze_issues(
    project_id: UUID | None = Query(None, description="Optional project to scope analysis to"),
    include_safe: bool = Query(True, description="Include safe auto-apply changes"),
    include_approval: bool = Query(True, description="Include changes requiring approval"),
    service: IssueRefinementService = Depends(get_refinement_service),
) -> dict[str, Any]:
    """
    Analyze issues and generate refinement plan.

    Returns categorized changes:
    - safe_changes: Auto-applicable changes (tags, templates)
    - approval_needed: Changes requiring user approval (status, dependencies)
    """
    result = await service.analyze_issues(
        project_id=project_id,
        include_safe=include_safe,
        include_approval_needed=include_approval,
    )
    return result


@router.post("/execute-safe")
async def execute_safe_changes(
    changes: list[dict[str, Any]],
    service: IssueRefinementService = Depends(get_refinement_service),
) -> dict[str, Any]:
    """
    Execute safe changes automatically.

    Args:
        changes: List of safe changes from analyze endpoint
    """
    result = await service.execute_safe_changes(changes)
    return result


@router.post("/execute-approved")
async def execute_approved_changes(
    changes: list[dict[str, Any]],
    service: IssueRefinementService = Depends(get_refinement_service),
) -> dict[str, Any]:
    """
    Execute changes that have been approved by user.

    Args:
        changes: List of approved changes from approval_needed
    """
    result = await service.execute_approved_changes(changes)
    return result
