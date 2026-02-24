"""Work Queue API endpoints for prioritized issue management."""

import logging
from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

from turbo.api.dependencies import get_issue_service
from turbo.core.schemas.issue import IssueResponse
from turbo.core.services.issue import IssueService

logger = logging.getLogger(__name__)

router = APIRouter()


class SetRankRequest(BaseModel):
    """Request to set issue work rank."""

    work_rank: int = Field(..., ge=1, description="New rank position (1=highest priority)")


class BulkRerankRequest(BaseModel):
    """Request to bulk update issue ranks."""

    issue_ranks: list[dict[str, int]] = Field(
        ...,
        description="List of {issue_id: rank} mappings",
        example=[{"issue_id": "uuid1", "rank": 1}, {"issue_id": "uuid2", "rank": 2}],
    )


@router.get("/", response_model=list[IssueResponse])
async def get_work_queue(
    status_filter: str | None = Query(None, pattern="^(open|ready|in_progress|review|testing|closed)$"),
    priority_filter: str | None = Query(None, pattern="^(low|medium|high|critical)$"),
    limit: int | None = Query(100, ge=1, le=500),
    offset: int | None = Query(0, ge=0),
    include_unranked: bool = Query(False, description="Include issues without work_rank"),
    issue_service: IssueService = Depends(get_issue_service),
) -> list[IssueResponse]:
    """
    Get work queue - all issues sorted by work_rank.

    Returns issues ordered by work_rank (ascending), with optional filtering.
    Only returns ranked issues by default (work_rank IS NOT NULL).
    """
    try:
        issues = await issue_service.get_work_queue(
            status=status_filter,
            priority=priority_filter,
            limit=limit,
            offset=offset,
            include_unranked=include_unranked,
        )
        return issues
    except Exception:
        logger.exception("Failed to fetch work queue")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch work queue",
        )


@router.get("/next", response_model=IssueResponse | None)
async def get_next_issue(
    issue_service: IssueService = Depends(get_issue_service),
) -> IssueResponse | None:
    """
    Get THE next issue to work on.

    Returns the highest-ranked open/in_progress issue (work_rank=1).
    Returns None if no ranked issues exist.
    """
    try:
        next_issue = await issue_service.get_next_issue()
        return next_issue
    except Exception:
        logger.exception("Failed to fetch next issue")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch next issue",
        )


@router.post("/{issue_id}/rank", response_model=IssueResponse)
async def set_issue_rank(
    issue_id: UUID,
    rank_request: SetRankRequest,
    issue_service: IssueService = Depends(get_issue_service),
) -> IssueResponse:
    """
    Set work rank for a specific issue.

    Updates the issue's work_rank and last_ranked_at timestamp.
    """
    try:
        updated_issue = await issue_service.set_work_rank(
            issue_id=issue_id, work_rank=rank_request.work_rank
        )
        return updated_issue
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except Exception:
        logger.exception("Failed to set issue rank")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to set issue rank",
        )


@router.delete("/{issue_id}/rank", response_model=IssueResponse)
async def remove_issue_rank(
    issue_id: UUID,
    issue_service: IssueService = Depends(get_issue_service),
) -> IssueResponse:
    """
    Remove issue from work queue (set work_rank to NULL).
    """
    try:
        updated_issue = await issue_service.set_work_rank(issue_id=issue_id, work_rank=None)
        return updated_issue
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except Exception:
        logger.exception("Failed to remove issue rank")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to remove issue rank",
        )


@router.post("/bulk-rerank", response_model=dict)
async def bulk_rerank_issues(
    rerank_request: BulkRerankRequest,
    issue_service: IssueService = Depends(get_issue_service),
) -> dict:
    """
    Bulk update work ranks for multiple issues.

    Useful for drag-and-drop reordering in the UI.
    """
    try:
        updated_count = await issue_service.bulk_rerank(rerank_request.issue_ranks)
        return {
            "updated_count": updated_count,
            "message": f"Successfully updated {updated_count} issue ranks",
        }
    except Exception:
        logger.exception("Failed to bulk rerank issues")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to bulk rerank issues",
        )


@router.post("/auto-rank", response_model=dict)
async def auto_rank_issues(
    issue_service: IssueService = Depends(get_issue_service),
) -> dict:
    """
    Auto-rank all open/in_progress issues based on intelligent scoring.

    Ranking factors:
    - Priority (critical > high > medium > low)
    - Age (older issues ranked higher)
    - Blockers (issues not blocked ranked higher)
    - Milestone deadlines (issues with approaching deadlines ranked higher)
    - Dependencies (issues that block others ranked higher)
    """
    try:
        ranked_count = await issue_service.auto_rank_issues()
        return {
            "ranked_count": ranked_count,
            "message": f"Successfully auto-ranked {ranked_count} issues",
        }
    except Exception:
        logger.exception("Failed to auto-rank issues")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to auto-rank issues",
        )
