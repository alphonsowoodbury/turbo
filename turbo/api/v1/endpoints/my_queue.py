"""
My Queue API Endpoint

Unified work queue showing:
- Action approvals (pending AI actions requiring user approval)
- Assigned tasks (issues/initiatives/milestones assigned to user)
- Review requests (staff requesting user feedback/approval)
"""

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from turbo.api.dependencies import get_db_session
from turbo.core.models.action_approval import ActionStatus
from turbo.core.repositories.action_approval_repository import ActionApprovalRepository
from turbo.core.repositories.review_request import ReviewRequestRepository
from turbo.core.repositories.issue import IssueRepository
from turbo.core.repositories.initiative import InitiativeRepository
from turbo.core.repositories.milestone import MilestoneRepository
from turbo.core.schemas.action_approval import ActionApprovalResponse
from turbo.core.schemas.review_request import ReviewRequestResponse
from turbo.core.schemas.issue import IssueResponse
from turbo.core.schemas.initiative import InitiativeResponse
from turbo.core.schemas.milestone import MilestoneResponse

router = APIRouter(prefix="/my-queue", tags=["my-queue"])


class MyQueueCounts(BaseModel):
    """Counts for different queue sections."""

    action_approvals: int = 0
    assigned_issues: int = 0
    assigned_initiatives: int = 0
    assigned_milestones: int = 0
    review_requests: int = 0
    total: int = 0


class MyQueueResponse(BaseModel):
    """Complete My Queue response with all work items."""

    # Action approvals (AI actions needing approval)
    action_approvals: list[ActionApprovalResponse]

    # Assigned tasks
    assigned_issues: list[IssueResponse]
    assigned_initiatives: list[InitiativeResponse]
    assigned_milestones: list[MilestoneResponse]

    # Review requests from staff
    review_requests: list[ReviewRequestResponse]

    # Counts
    counts: MyQueueCounts


@router.get("/", response_model=MyQueueResponse)
async def get_my_queue(
    limit: int = Query(50, ge=1, le=100, description="Max items per section"),
    db: AsyncSession = Depends(get_db_session),
) -> MyQueueResponse:
    """
    Get the unified My Queue with all pending work.

    Returns:
    - Pending action approvals
    - Issues/initiatives/milestones assigned to user
    - Pending review requests from staff

    All sections are limited to the specified limit to keep response size manageable.
    """
    # Get repositories
    action_repo = ActionApprovalRepository(db)
    review_request_repo = ReviewRequestRepository(db)
    issue_repo = IssueRepository(db)
    initiative_repo = InitiativeRepository(db)
    milestone_repo = MilestoneRepository(db)

    # Get pending action approvals
    action_approvals_list = await action_repo.get_pending_approvals(limit=limit)
    action_approvals = [
        ActionApprovalResponse.model_validate(a) for a in action_approvals_list
    ]

    # Get pending review requests
    review_requests_list = await review_request_repo.get_pending_for_user()
    review_requests = [
        ReviewRequestResponse.model_validate(r)
        for r in review_requests_list[:limit]
    ]

    # Get assigned issues (assigned_to_type = 'user')
    # Note: In Phase 1, we're using assignee field. In Phase 2+, we'll use assigned_to_type/assigned_to_id
    # For now, we'll get unassigned issues as a placeholder
    assigned_issues_list = await issue_repo.get_by_status("open")
    # Filter for issues that might be "assigned to user" - for now just open issues
    assigned_issues = [
        IssueResponse.model_validate(i) for i in assigned_issues_list[:limit]
    ]

    # Get assigned initiatives
    # TODO: Add assignment filtering when implemented
    assigned_initiatives_list = []
    assigned_initiatives = []

    # Get assigned milestones
    # TODO: Add assignment filtering when implemented
    assigned_milestones_list = []
    assigned_milestones = []

    # Build counts
    counts = MyQueueCounts(
        action_approvals=len(action_approvals_list),
        assigned_issues=len(assigned_issues_list),
        assigned_initiatives=len(assigned_initiatives_list),
        assigned_milestones=len(assigned_milestones_list),
        review_requests=len(review_requests_list),
    )
    counts.total = (
        counts.action_approvals
        + counts.assigned_issues
        + counts.assigned_initiatives
        + counts.assigned_milestones
        + counts.review_requests
    )

    return MyQueueResponse(
        action_approvals=action_approvals,
        assigned_issues=assigned_issues,
        assigned_initiatives=assigned_initiatives,
        assigned_milestones=assigned_milestones,
        review_requests=review_requests,
        counts=counts,
    )


@router.get("/counts", response_model=MyQueueCounts)
async def get_my_queue_counts(
    db: AsyncSession = Depends(get_db_session),
) -> MyQueueCounts:
    """
    Get counts for each section of My Queue.

    Lightweight endpoint for showing badge counts in UI.
    """
    # Get repositories
    action_repo = ActionApprovalRepository(db)
    review_request_repo = ReviewRequestRepository(db)
    issue_repo = IssueRepository(db)

    # Get counts
    action_approvals_count = await action_repo.count_pending()
    review_requests_count = await review_request_repo.count_pending()

    # TODO: Add proper assignment filtering
    # For now, count open issues as assigned issues
    open_issues = await issue_repo.get_by_status("open")
    assigned_issues_count = len(open_issues)

    counts = MyQueueCounts(
        action_approvals=action_approvals_count,
        assigned_issues=assigned_issues_count,
        assigned_initiatives=0,  # TODO
        assigned_milestones=0,  # TODO
        review_requests=review_requests_count,
    )
    counts.total = (
        counts.action_approvals
        + counts.assigned_issues
        + counts.assigned_initiatives
        + counts.assigned_milestones
        + counts.review_requests
    )

    return counts


@router.get("/review-requests", response_model=list[ReviewRequestResponse])
async def get_my_review_requests(
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db_session),
) -> list[ReviewRequestResponse]:
    """
    Get pending review requests from staff.

    Staff can create review requests asking for:
    - Scope validation
    - Feedback on proposals
    - Approval for actions
    - Architecture reviews
    - Security reviews
    - Product reviews
    """
    repo = ReviewRequestRepository(db)
    requests = await repo.get_pending_for_user()
    return [ReviewRequestResponse.model_validate(r) for r in requests[:limit]]
