"""Initiative API endpoints."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from turbo.api.dependencies import get_initiative_service
from turbo.core.schemas import (
    InitiativeCreate,
    InitiativeResponse,
    InitiativeUpdate,
    IssueResponse,
)
from turbo.core.services.initiative import InitiativeService
from turbo.utils.exceptions import (
    InitiativeNotFoundError,
    ProjectNotFoundError,
)
from turbo.utils.exceptions import (
    ValidationError as TurboValidationError,
)

router = APIRouter()


@router.post("/", response_model=InitiativeResponse, status_code=status.HTTP_201_CREATED)
async def create_initiative(
    initiative_data: InitiativeCreate,
    initiative_service: InitiativeService = Depends(get_initiative_service),
) -> InitiativeResponse:
    """Create a new initiative."""
    try:
        return await initiative_service.create_initiative(initiative_data)
    except ProjectNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except TurboValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e)
        )


@router.get("/{initiative_id}", response_model=InitiativeResponse)
async def get_initiative(
    initiative_id: UUID,
    initiative_service: InitiativeService = Depends(get_initiative_service),
) -> InitiativeResponse:
    """Get an initiative by ID."""
    try:
        return await initiative_service.get_initiative_by_id(initiative_id)
    except InitiativeNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Initiative with id {initiative_id} not found",
        )


@router.get("/{initiative_id}/issues", response_model=list[IssueResponse])
async def get_initiative_issues(
    initiative_id: UUID,
    initiative_service: InitiativeService = Depends(get_initiative_service),
) -> list[IssueResponse]:
    """Get all issues associated with an initiative."""
    try:
        return await initiative_service.get_initiative_issues(initiative_id)
    except InitiativeNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Initiative with id {initiative_id} not found",
        )


@router.get("/", response_model=list[InitiativeResponse])
async def get_initiatives(
    project_id: UUID | None = Query(None),
    status_filter: str | None = Query(None, alias="status"),
    workspace: str | None = Query(None, pattern="^(all|personal|freelance|work)$"),
    work_company: str | None = Query(None),
    limit: int | None = Query(None, ge=1, le=100),
    offset: int | None = Query(None, ge=0),
    initiative_service: InitiativeService = Depends(get_initiative_service),
) -> list[InitiativeResponse]:
    """Get all initiatives with optional filtering by project, status, or workspace."""
    try:
        # Workspace filtering takes precedence
        if workspace and workspace != "all":
            return await initiative_service.get_initiatives_by_workspace(
                workspace=workspace,
                work_company=work_company,
                limit=limit,
                offset=offset,
            )
        elif project_id:
            return await initiative_service.get_initiatives_by_project(project_id)
        elif status_filter:
            return await initiative_service.get_initiatives_by_status(status_filter)
        else:
            return await initiative_service.get_all_initiatives(limit=limit, offset=offset)
    except ProjectNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.put("/{initiative_id}", response_model=InitiativeResponse)
async def update_initiative(
    initiative_id: UUID,
    initiative_data: InitiativeUpdate,
    initiative_service: InitiativeService = Depends(get_initiative_service),
) -> InitiativeResponse:
    """Update an initiative."""
    try:
        return await initiative_service.update_initiative(initiative_id, initiative_data)
    except InitiativeNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Initiative with id {initiative_id} not found",
        )
    except TurboValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e)
        )


@router.delete("/{initiative_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_initiative(
    initiative_id: UUID,
    initiative_service: InitiativeService = Depends(get_initiative_service),
) -> None:
    """Delete an initiative."""
    try:
        await initiative_service.delete_initiative(initiative_id)
    except InitiativeNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Initiative with id {initiative_id} not found",
        )
