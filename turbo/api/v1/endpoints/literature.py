"""API endpoints for Literature."""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from turbo.core.database.connection import get_db_session
from turbo.core.repositories.literature import LiteratureRepository
from turbo.core.schemas.literature import (
    FeedURL,
    LiteratureCreate,
    LiteratureFilter,
    LiteratureResponse,
    LiteratureType,
    LiteratureUpdate,
)
from turbo.core.services.literature import LiteratureService

router = APIRouter(prefix="/literature", tags=["literature"])


def get_literature_service(
    session: AsyncSession = Depends(get_db_session),
) -> LiteratureService:
    """Get literature service."""
    repository = LiteratureRepository(session)
    return LiteratureService(repository)


@router.post("/", response_model=LiteratureResponse, status_code=status.HTTP_201_CREATED)
async def create_literature(
    literature: LiteratureCreate,
    service: LiteratureService = Depends(get_literature_service),
) -> LiteratureResponse:
    """Create new literature."""
    return await service.create_literature(literature)


@router.get("/", response_model=list[LiteratureResponse])
async def list_literature(
    type: Optional[LiteratureType] = Query(None),
    source: Optional[str] = Query(None),
    is_read: Optional[bool] = Query(None),
    is_favorite: Optional[bool] = Query(None),
    is_archived: Optional[bool] = Query(None),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    service: LiteratureService = Depends(get_literature_service),
) -> list[LiteratureResponse]:
    """List literature with optional filters."""
    if is_favorite:
        return await service.get_favorites(limit, offset)
    elif is_read is False:
        return await service.get_unread(limit, offset)
    elif type:
        return await service.get_by_type(type, limit, offset)
    elif source:
        return await service.get_by_source(source, limit, offset)
    else:
        return await service.get_all_literature(limit, offset)


@router.get("/{literature_id}", response_model=LiteratureResponse)
async def get_literature(
    literature_id: UUID,
    service: LiteratureService = Depends(get_literature_service),
) -> LiteratureResponse:
    """Get literature by ID."""
    literature = await service.get_literature(literature_id)
    if not literature:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Literature not found",
        )
    return literature


@router.put("/{literature_id}", response_model=LiteratureResponse)
async def update_literature(
    literature_id: UUID,
    literature: LiteratureUpdate,
    service: LiteratureService = Depends(get_literature_service),
) -> LiteratureResponse:
    """Update literature."""
    updated = await service.update_literature(literature_id, literature)
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Literature not found",
        )
    return updated


@router.delete("/{literature_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_literature(
    literature_id: UUID,
    service: LiteratureService = Depends(get_literature_service),
) -> None:
    """Delete literature."""
    deleted = await service.delete_literature(literature_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Literature not found",
        )


@router.post("/{literature_id}/read", response_model=LiteratureResponse)
async def mark_as_read(
    literature_id: UUID,
    service: LiteratureService = Depends(get_literature_service),
) -> LiteratureResponse:
    """Mark literature as read."""
    literature = await service.mark_as_read(literature_id)
    if not literature:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Literature not found",
        )
    return literature


@router.post("/{literature_id}/favorite", response_model=LiteratureResponse)
async def toggle_favorite(
    literature_id: UUID,
    service: LiteratureService = Depends(get_literature_service),
) -> LiteratureResponse:
    """Toggle favorite status."""
    literature = await service.toggle_favorite(literature_id)
    if not literature:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Literature not found",
        )
    return literature


@router.post("/fetch-url", response_model=LiteratureResponse)
async def fetch_from_url(
    url: FeedURL,
    service: LiteratureService = Depends(get_literature_service),
) -> LiteratureResponse:
    """Fetch and create article from URL."""
    try:
        return await service.fetch_from_url(url.url)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to fetch content: {str(e)}",
        )


@router.post("/fetch-feed", response_model=list[LiteratureResponse])
async def fetch_from_feed(
    feed: FeedURL,
    service: LiteratureService = Depends(get_literature_service),
) -> list[LiteratureResponse]:
    """Fetch articles from RSS feed."""
    try:
        return await service.fetch_from_rss_feed(feed.url)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to fetch feed: {str(e)}",
        )