"""Tag API endpoints."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel

from turbo.api.dependencies import get_tag_service
from turbo.core.schemas import IssueResponse, ProjectResponse, TagCreate, TagResponse
from turbo.core.services import TagService
from turbo.utils.exceptions import (
    DuplicateResourceError,
    TagNotFoundError,
)
from turbo.utils.exceptions import (
    ValidationError as TurboValidationError,
)

router = APIRouter()


class BulkTagRequest(BaseModel):
    """Request model for bulk tag operations."""

    tag_ids: list[UUID]


class TagUsageStats(BaseModel):
    """Tag usage statistics model."""

    project_count: int
    issue_count: int
    total_usage: int


@router.post("/", response_model=TagResponse, status_code=status.HTTP_201_CREATED)
async def create_tag(
    tag_data: TagCreate, tag_service: TagService = Depends(get_tag_service)
) -> TagResponse:
    """Create a new tag."""
    try:
        return await tag_service.create_tag(tag_data)
    except DuplicateResourceError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except TurboValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e)
        )


@router.get("/{tag_id}", response_model=TagResponse)
async def get_tag(
    tag_id: UUID, tag_service: TagService = Depends(get_tag_service)
) -> TagResponse:
    """Get a tag by ID."""
    try:
        return await tag_service.get_tag_by_id(tag_id)
    except TagNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tag with id {tag_id} not found",
        )


@router.get("/", response_model=list[TagResponse])
async def get_tags(
    color: str | None = Query(None),
    limit: int | None = Query(None, ge=1, le=100),
    offset: int | None = Query(None, ge=0),
    tag_service: TagService = Depends(get_tag_service),
) -> list[TagResponse]:
    """Get all tags with optional filtering."""
    if color:
        return await tag_service.get_tags_by_color(color)
    else:
        return await tag_service.get_all_tags(limit=limit, offset=offset)


@router.put("/{tag_id}", response_model=TagResponse)
async def update_tag(
    tag_id: UUID,
    tag_data: TagCreate,
    tag_service: TagService = Depends(get_tag_service),
) -> TagResponse:
    """Update a tag."""
    try:
        return await tag_service.update_tag(tag_id, tag_data)
    except TagNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tag with id {tag_id} not found",
        )
    except DuplicateResourceError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except TurboValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e)
        )


@router.delete("/{tag_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_tag(
    tag_id: UUID, tag_service: TagService = Depends(get_tag_service)
) -> None:
    """Delete a tag."""
    try:
        await tag_service.delete_tag(tag_id)
    except TagNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tag with id {tag_id} not found",
        )


@router.get("/search", response_model=list[TagResponse])
async def search_tags(
    query: str = Query(..., min_length=1),
    tag_service: TagService = Depends(get_tag_service),
) -> list[TagResponse]:
    """Search tags by name."""
    return await tag_service.search_tags(query)


@router.get("/popular", response_model=list[TagResponse])
async def get_popular_tags(
    limit: int = Query(10, ge=1, le=50),
    tag_service: TagService = Depends(get_tag_service),
) -> list[TagResponse]:
    """Get most popular tags."""
    return await tag_service.get_popular_tags(limit=limit)


@router.get("/unused", response_model=list[TagResponse])
async def get_unused_tags(
    tag_service: TagService = Depends(get_tag_service),
) -> list[TagResponse]:
    """Get tags that are not used by any projects or issues."""
    return await tag_service.get_unused_tags()


@router.get("/{tag_id}/usage", response_model=TagUsageStats)
async def get_tag_usage_statistics(
    tag_id: UUID, tag_service: TagService = Depends(get_tag_service)
) -> TagUsageStats:
    """Get tag usage statistics."""
    try:
        stats = await tag_service.get_tag_usage_statistics(tag_id)
        return TagUsageStats(
            project_count=stats.get("project_count", 0),
            issue_count=stats.get("issue_count", 0),
            total_usage=stats.get("total_usage", 0),
        )
    except TagNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tag with id {tag_id} not found",
        )


@router.get("/{tag_id}/projects", response_model=list[ProjectResponse])
async def get_projects_with_tag(
    tag_id: UUID, tag_service: TagService = Depends(get_tag_service)
) -> list[ProjectResponse]:
    """Get projects that have a specific tag."""
    try:
        return await tag_service.get_projects_with_tag(tag_id)
    except TagNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tag with id {tag_id} not found",
        )


@router.get("/{tag_id}/issues", response_model=list[IssueResponse])
async def get_issues_with_tag(
    tag_id: UUID, tag_service: TagService = Depends(get_tag_service)
) -> list[IssueResponse]:
    """Get issues that have a specific tag."""
    try:
        return await tag_service.get_issues_with_tag(tag_id)
    except TagNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tag with id {tag_id} not found",
        )
