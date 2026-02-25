"""Milestone API endpoints."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from turbo.api.dependencies import get_milestone_service
from turbo.core.schemas import (
    IssueResponse,
    MilestoneCreate,
    MilestoneResponse,
    MilestoneUpdate,
)
from turbo.core.services.milestone import MilestoneService
from turbo.utils.exceptions import (
    MilestoneNotFoundError,
    ProjectNotFoundError,
)
from turbo.utils.exceptions import (
    ValidationError as TurboValidationError,
)

router = APIRouter()


@router.post("/", response_model=MilestoneResponse, status_code=status.HTTP_201_CREATED)
async def create_milestone(
    milestone_data: MilestoneCreate,
    milestone_service: MilestoneService = Depends(get_milestone_service),
) -> MilestoneResponse:
    """Create a new milestone."""
    try:
        return await milestone_service.create_milestone(milestone_data)
    except ProjectNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except TurboValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e)
        )


@router.get("/{milestone_id}", response_model=MilestoneResponse)
async def get_milestone(
    milestone_id: UUID,
    milestone_service: MilestoneService = Depends(get_milestone_service),
) -> MilestoneResponse:
    """Get a milestone by ID."""
    try:
        return await milestone_service.get_milestone_by_id(milestone_id)
    except MilestoneNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Milestone with id {milestone_id} not found",
        )


@router.get("/{milestone_id}/issues", response_model=list[IssueResponse])
async def get_milestone_issues(
    milestone_id: UUID,
    milestone_service: MilestoneService = Depends(get_milestone_service),
) -> list[IssueResponse]:
    """Get all issues associated with a milestone."""
    try:
        return await milestone_service.get_milestone_issues(milestone_id)
    except MilestoneNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Milestone with id {milestone_id} not found",
        )


@router.get("/", response_model=list[MilestoneResponse])
async def get_milestones(
    project_id: UUID | None = Query(None),
    status_filter: str | None = Query(None, alias="status"),
    workspace: str | None = Query(None, pattern="^(all|personal|freelance|work)$"),
    work_company: str | None = Query(None),
    limit: int | None = Query(None, ge=1, le=100),
    offset: int | None = Query(None, ge=0),
    sort_by: str | None = Query(None),
    sort_order: str = Query("desc", pattern="^(asc|desc)$"),
    milestone_service: MilestoneService = Depends(get_milestone_service),
) -> list[MilestoneResponse]:
    """Get all milestones with optional filtering by project, status, or workspace."""
    try:
        # Workspace filtering takes precedence
        if workspace and workspace != "all":
            return await milestone_service.get_milestones_by_workspace(
                workspace=workspace,
                work_company=work_company,
                limit=limit,
                offset=offset,
                sort_by=sort_by,
                sort_order=sort_order,
            )
        elif project_id:
            return await milestone_service.get_milestones_by_project(
                project_id, sort_by=sort_by, sort_order=sort_order
            )
        elif status_filter:
            return await milestone_service.get_milestones_by_status(
                status_filter, sort_by=sort_by, sort_order=sort_order
            )
        else:
            return await milestone_service.get_all_milestones(
                limit=limit, offset=offset, sort_by=sort_by, sort_order=sort_order
            )
    except ProjectNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.put("/{milestone_id}", response_model=MilestoneResponse)
async def update_milestone(
    milestone_id: UUID,
    milestone_data: MilestoneUpdate,
    milestone_service: MilestoneService = Depends(get_milestone_service),
) -> MilestoneResponse:
    """Update a milestone."""
    try:
        return await milestone_service.update_milestone(milestone_id, milestone_data)
    except MilestoneNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Milestone with id {milestone_id} not found",
        )
    except TurboValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e)
        )


@router.delete("/{milestone_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_milestone(
    milestone_id: UUID,
    milestone_service: MilestoneService = Depends(get_milestone_service),
) -> None:
    """Delete a milestone."""
    try:
        await milestone_service.delete_milestone(milestone_id)
    except MilestoneNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Milestone with id {milestone_id} not found",
        )