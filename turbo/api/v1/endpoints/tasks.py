"""Task API endpoints for Turbo Daemon.

This module provides specialized endpoints for the daemon to:
- Poll for queued tasks
- Claim tasks for execution
- Report task completion/failure
"""

from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

from turbo.api.dependencies import get_issue_service
from turbo.core.services import IssueService
from turbo.utils.exceptions import IssueNotFoundError

router = APIRouter()


class TaskResponse(BaseModel):
    """Task response model for daemon consumption."""

    id: UUID
    issue_key: str | None
    title: str
    description: str
    acceptance_criteria: str | None
    status: str
    priority: str
    project_name: str | None = None
    project_key: str | None = None
    assigned_agent: str | None = None
    claimed_at: datetime | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class TaskClaimRequest(BaseModel):
    """Request to claim a task for execution."""

    agent_id: str = Field(..., description="ID of the claiming agent")


class TaskCompleteRequest(BaseModel):
    """Request to mark a task as completed."""

    pr_url: str = Field(..., description="URL of the created PR")
    execution_notes: str | None = Field(None, description="Notes from execution")


class TaskFailRequest(BaseModel):
    """Request to mark a task as failed."""

    error_message: str = Field(..., description="Error message")
    execution_notes: str | None = Field(None, description="Additional notes")


class TaskNeedsHumanRequest(BaseModel):
    """Request to flag a task for human review."""

    reason: str = Field(..., description="Why human intervention is needed")
    pr_url: str | None = Field(None, description="URL of PR if one was created")


@router.get("/", response_model=list[TaskResponse])
async def get_queued_tasks(
    status_filter: str = Query("queued", alias="status"),
    limit: int = Query(10, ge=1, le=50),
    issue_service: IssueService = Depends(get_issue_service),
) -> list[TaskResponse]:
    """
    Get tasks ready for daemon execution.

    Default returns tasks with status='queued' (ready for pickup).
    Daemon polls this endpoint to find work.
    """
    issues = await issue_service.get_issues_by_status(status_filter)

    # Convert to TaskResponse
    tasks = []
    for issue in issues[:limit]:
        project_name = None
        project_key = None
        if hasattr(issue, "project") and issue.project:
            project_name = issue.project.name
            project_key = issue.project.project_key

        tasks.append(
            TaskResponse(
                id=issue.id,
                issue_key=issue.issue_key,
                title=issue.title,
                description=issue.description,
                acceptance_criteria=getattr(issue, "acceptance_criteria", None),
                status=issue.status,
                priority=issue.priority,
                project_name=project_name,
                project_key=project_key,
                assigned_agent=getattr(issue, "assigned_agent", None),
                claimed_at=getattr(issue, "claimed_at", None),
                created_at=issue.created_at,
                updated_at=issue.updated_at,
            )
        )

    return tasks


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(
    task_id: UUID,
    issue_service: IssueService = Depends(get_issue_service),
) -> TaskResponse:
    """Get full task details for daemon execution."""
    try:
        issue = await issue_service.get_issue_by_id(task_id)

        project_name = None
        project_key = None
        if hasattr(issue, "project") and issue.project:
            project_name = issue.project.name
            project_key = issue.project.project_key

        return TaskResponse(
            id=issue.id,
            issue_key=issue.issue_key,
            title=issue.title,
            description=issue.description,
            acceptance_criteria=getattr(issue, "acceptance_criteria", None),
            status=issue.status,
            priority=issue.priority,
            project_name=project_name,
            project_key=project_key,
            assigned_agent=getattr(issue, "assigned_agent", None),
            claimed_at=getattr(issue, "claimed_at", None),
            created_at=issue.created_at,
            updated_at=issue.updated_at,
        )
    except IssueNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task {task_id} not found",
        )


@router.post("/{task_id}/claim", response_model=TaskResponse)
async def claim_task(
    task_id: UUID,
    request: TaskClaimRequest,
    issue_service: IssueService = Depends(get_issue_service),
) -> TaskResponse:
    """
    Claim a task for execution.

    Sets assigned_agent and claimed_at, transitions status to 'in_progress'.
    Returns 409 Conflict if already claimed.
    """
    try:
        issue = await issue_service.get_issue_by_id(task_id)

        # Check if already claimed
        if issue.status != "queued":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Task is not queued (current status: {issue.status})",
            )

        if getattr(issue, "assigned_agent", None):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Task already claimed by {issue.assigned_agent}",
            )

        # Claim the task
        from turbo.core.schemas import IssueUpdate

        update_data = IssueUpdate(
            status="in_progress",
            assigned_agent=request.agent_id,
            claimed_at=datetime.now(timezone.utc),
        )
        updated = await issue_service.update_issue(task_id, update_data)

        project_name = None
        project_key = None
        if hasattr(updated, "project") and updated.project:
            project_name = updated.project.name
            project_key = updated.project.project_key

        return TaskResponse(
            id=updated.id,
            issue_key=updated.issue_key,
            title=updated.title,
            description=updated.description,
            acceptance_criteria=getattr(updated, "acceptance_criteria", None),
            status=updated.status,
            priority=updated.priority,
            project_name=project_name,
            project_key=project_key,
            assigned_agent=getattr(updated, "assigned_agent", None),
            claimed_at=getattr(updated, "claimed_at", None),
            created_at=updated.created_at,
            updated_at=updated.updated_at,
        )

    except IssueNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task {task_id} not found",
        )


@router.post("/{task_id}/complete")
async def complete_task(
    task_id: UUID,
    request: TaskCompleteRequest,
    issue_service: IssueService = Depends(get_issue_service),
):
    """
    Mark a task as completed.

    Sets pr_url and transitions status to 'review' or 'done'.
    """
    try:
        from turbo.core.schemas import IssueUpdate

        update_data = IssueUpdate(
            status="review",
            pr_url=request.pr_url,
            execution_notes=request.execution_notes,
        )
        await issue_service.update_issue(task_id, update_data)

        return {"status": "completed", "task_id": str(task_id), "pr_url": request.pr_url}

    except IssueNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task {task_id} not found",
        )


@router.post("/{task_id}/fail")
async def fail_task(
    task_id: UUID,
    request: TaskFailRequest,
    issue_service: IssueService = Depends(get_issue_service),
):
    """
    Mark a task as failed.

    Returns task to 'queued' status and clears agent assignment.
    """
    try:
        from turbo.core.schemas import IssueUpdate

        update_data = IssueUpdate(
            status="queued",
            assigned_agent=None,
            claimed_at=None,
            execution_notes=f"FAILED: {request.error_message}\n{request.execution_notes or ''}",
        )
        await issue_service.update_issue(task_id, update_data)

        return {"status": "failed", "task_id": str(task_id), "message": request.error_message}

    except IssueNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task {task_id} not found",
        )


@router.post("/{task_id}/needs-human")
async def needs_human_review(
    task_id: UUID,
    request: TaskNeedsHumanRequest,
    issue_service: IssueService = Depends(get_issue_service),
):
    """
    Flag a task as needing human review.

    Used when agent has low confidence or encounters ambiguity.
    """
    try:
        from turbo.core.schemas import IssueUpdate

        notes = f"NEEDS HUMAN REVIEW: {request.reason}"
        if request.pr_url:
            notes += f"\nPR: {request.pr_url}"

        update_data = IssueUpdate(
            status="needs_review",
            pr_url=request.pr_url,
            execution_notes=notes,
        )
        await issue_service.update_issue(task_id, update_data)

        return {
            "status": "needs_human",
            "task_id": str(task_id),
            "reason": request.reason,
            "pr_url": request.pr_url,
        }

    except IssueNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task {task_id} not found",
        )
