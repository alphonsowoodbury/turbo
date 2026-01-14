"""SavedFilter API endpoints."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete

from turbo.core.database import get_db_session
from turbo.core.models import SavedFilter
from turbo.core.schemas import SavedFilterCreate, SavedFilterResponse, SavedFilterUpdate

router = APIRouter()


@router.post("/", response_model=SavedFilterResponse, status_code=status.HTTP_201_CREATED)
async def create_saved_filter(
    filter_data: SavedFilterCreate,
    db: AsyncSession = Depends(get_db_session),
) -> SavedFilterResponse:
    """Create a new saved filter."""
    saved_filter = SavedFilter(
        name=filter_data.name,
        description=filter_data.description,
        filter_config=filter_data.filter_config,
        project_id=filter_data.project_id,
    )
    db.add(saved_filter)
    await db.commit()
    await db.refresh(saved_filter)

    return SavedFilterResponse.model_validate(saved_filter)


@router.get("/project/{project_id}", response_model=list[SavedFilterResponse])
async def get_project_saved_filters(
    project_id: UUID,
    db: AsyncSession = Depends(get_db_session),
) -> list[SavedFilterResponse]:
    """Get all saved filters for a project."""
    stmt = select(SavedFilter).where(
        SavedFilter.project_id == project_id
    ).order_by(SavedFilter.created_at.desc())

    result = await db.execute(stmt)
    saved_filters = result.scalars().all()

    return [SavedFilterResponse.model_validate(f) for f in saved_filters]


@router.get("/{filter_id}", response_model=SavedFilterResponse)
async def get_saved_filter(
    filter_id: UUID,
    db: AsyncSession = Depends(get_db_session),
) -> SavedFilterResponse:
    """Get a saved filter by ID."""
    stmt = select(SavedFilter).where(SavedFilter.id == filter_id)
    result = await db.execute(stmt)
    saved_filter = result.scalar_one_or_none()

    if not saved_filter:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Saved filter with id {filter_id} not found",
        )

    return SavedFilterResponse.model_validate(saved_filter)


@router.put("/{filter_id}", response_model=SavedFilterResponse)
async def update_saved_filter(
    filter_id: UUID,
    filter_data: SavedFilterUpdate,
    db: AsyncSession = Depends(get_db_session),
) -> SavedFilterResponse:
    """Update a saved filter."""
    stmt = select(SavedFilter).where(SavedFilter.id == filter_id)
    result = await db.execute(stmt)
    saved_filter = result.scalar_one_or_none()

    if not saved_filter:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Saved filter with id {filter_id} not found",
        )

    # Update fields
    if filter_data.name is not None:
        saved_filter.name = filter_data.name
    if filter_data.description is not None:
        saved_filter.description = filter_data.description
    if filter_data.filter_config is not None:
        saved_filter.filter_config = filter_data.filter_config

    await db.commit()
    await db.refresh(saved_filter)

    return SavedFilterResponse.model_validate(saved_filter)


@router.delete("/{filter_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_saved_filter(
    filter_id: UUID,
    db: AsyncSession = Depends(get_db_session),
) -> None:
    """Delete a saved filter."""
    stmt = delete(SavedFilter).where(SavedFilter.id == filter_id)
    result = await db.execute(stmt)
    await db.commit()

    if result.rowcount == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Saved filter with id {filter_id} not found",
        )