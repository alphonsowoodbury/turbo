"""Project API endpoints."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from turbo.api.dependencies import get_project_service
from turbo.core.schemas import (
    DocumentResponse,
    IssueResponse,
    ProjectCreate,
    ProjectResponse,
    ProjectUpdate,
)
from turbo.core.services import ProjectService
from turbo.utils.exceptions import (
    DuplicateResourceError,
    ProjectNotFoundError,
)
from turbo.utils.exceptions import (
    ValidationError as TurboValidationError,
)

router = APIRouter()


@router.post("/", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_project(
    project_data: ProjectCreate,
    project_service: ProjectService = Depends(get_project_service),
) -> ProjectResponse:
    """Create a new project."""
    try:
        return await project_service.create_project(project_data)
    except DuplicateResourceError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except TurboValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e)
        )


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: UUID, project_service: ProjectService = Depends(get_project_service)
) -> ProjectResponse:
    """Get a project by ID."""
    try:
        return await project_service.get_project_by_id(project_id)
    except ProjectNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project with id {project_id} not found",
        )


@router.get("/", response_model=list[ProjectResponse])
async def get_projects(
    status_filter: str | None = Query(None, alias="status"),
    priority: str | None = Query(None),
    workspace: str | None = Query(None, pattern="^(all|personal|freelance|work)$"),
    work_company: str | None = Query(None),
    limit: int | None = Query(None, ge=1, le=100),
    offset: int | None = Query(None, ge=0),
    sort_by: str | None = Query(None),
    sort_order: str = Query("desc", pattern="^(asc|desc)$"),
    project_service: ProjectService = Depends(get_project_service),
) -> list[ProjectResponse]:
    """Get all projects with optional filtering by status, priority, and workspace."""
    # Workspace filtering takes precedence
    if workspace and workspace != "all":
        return await project_service.get_projects_by_workspace(
            workspace=workspace,
            work_company=work_company,
            limit=limit,
            offset=offset,
            sort_by=sort_by,
            sort_order=sort_order,
        )
    elif status_filter:
        return await project_service.get_projects_by_status(status_filter, sort_by=sort_by, sort_order=sort_order)
    elif priority:
        return await project_service.get_projects_by_priority(priority, sort_by=sort_by, sort_order=sort_order)
    else:
        return await project_service.get_all_projects(limit=limit, offset=offset, sort_by=sort_by, sort_order=sort_order)


@router.put("/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: UUID,
    project_data: ProjectUpdate,
    project_service: ProjectService = Depends(get_project_service),
) -> ProjectResponse:
    """Update a project."""
    try:
        return await project_service.update_project(project_id, project_data)
    except ProjectNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project with id {project_id} not found",
        )
    except TurboValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e)
        )


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(
    project_id: UUID, project_service: ProjectService = Depends(get_project_service)
) -> None:
    """Delete a project."""
    try:
        await project_service.delete_project(project_id)
    except ProjectNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project with id {project_id} not found",
        )


@router.post("/{project_id}/archive", response_model=ProjectResponse)
async def archive_project(
    project_id: UUID, project_service: ProjectService = Depends(get_project_service)
) -> ProjectResponse:
    """Archive a project."""
    try:
        return await project_service.archive_project(project_id)
    except ProjectNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project with id {project_id} not found",
        )


@router.get("/{project_id}/stats", response_model=dict)
async def get_project_statistics(
    project_id: UUID, project_service: ProjectService = Depends(get_project_service)
) -> dict:
    """Get project statistics."""
    try:
        return await project_service.get_project_statistics(project_id)
    except ProjectNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project with id {project_id} not found",
        )


@router.get("/search", response_model=list[ProjectResponse])
async def search_projects(
    query: str = Query(..., min_length=1),
    project_service: ProjectService = Depends(get_project_service),
) -> list[ProjectResponse]:
    """Search projects by name."""
    return await project_service.search_projects_by_name(query)


@router.get("/{project_id}/issues", response_model=list[IssueResponse])
async def get_project_issues(
    project_id: UUID, project_service: ProjectService = Depends(get_project_service)
) -> list[IssueResponse]:
    """Get all issues for a project."""
    try:
        return await project_service.get_project_issues(project_id)
    except ProjectNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project with id {project_id} not found",
        )


@router.get("/{project_id}/documents", response_model=list[DocumentResponse])
async def get_project_documents(
    project_id: UUID, project_service: ProjectService = Depends(get_project_service)
) -> list[DocumentResponse]:
    """Get all documents for a project."""
    try:
        return await project_service.get_project_documents(project_id)
    except ProjectNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project with id {project_id} not found",
        )


@router.post("/{project_id}/tags/{tag_id}", response_model=ProjectResponse)
async def add_tag_to_project(
    project_id: UUID,
    tag_id: UUID,
    project_service: ProjectService = Depends(get_project_service),
) -> ProjectResponse:
    """Add a tag to a project."""
    try:
        return await project_service.add_tag_to_project(project_id, tag_id)
    except ProjectNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project with id {project_id} not found",
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete("/{project_id}/tags/{tag_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_tag_from_project(
    project_id: UUID,
    tag_id: UUID,
    project_service: ProjectService = Depends(get_project_service),
) -> None:
    """Remove a tag from a project."""
    try:
        await project_service.remove_tag_from_project(project_id, tag_id)
    except ProjectNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project with id {project_id} not found",
        )
