"""Favorite API endpoints."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from turbo.core.database import get_db_session
from turbo.core.models import Favorite
from turbo.core.schemas import FavoriteCreate, FavoriteResponse
from sqlalchemy import select, delete

router = APIRouter()


@router.post("/", response_model=FavoriteResponse, status_code=status.HTTP_201_CREATED)
async def create_favorite(
    favorite_data: FavoriteCreate,
    db: AsyncSession = Depends(get_db_session),
) -> FavoriteResponse:
    """Create a new favorite."""
    # Check if already favorited
    stmt = select(Favorite).where(
        Favorite.item_type == favorite_data.item_type,
        Favorite.item_id == favorite_data.item_id
    )
    result = await db.execute(stmt)
    existing = result.scalar_one_or_none()

    if existing:
        return FavoriteResponse.model_validate(existing)

    # Create new favorite
    favorite = Favorite(
        item_type=favorite_data.item_type,
        item_id=favorite_data.item_id
    )
    db.add(favorite)
    await db.commit()
    await db.refresh(favorite)

    return FavoriteResponse.model_validate(favorite)


@router.get("/", response_model=list[FavoriteResponse])
async def get_favorites(
    db: AsyncSession = Depends(get_db_session),
) -> list[FavoriteResponse]:
    """Get all favorites."""
    stmt = select(Favorite).order_by(Favorite.created_at.desc())
    result = await db.execute(stmt)
    favorites = result.scalars().all()

    return [FavoriteResponse.model_validate(f) for f in favorites]


@router.delete("/{favorite_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_favorite(
    favorite_id: UUID,
    db: AsyncSession = Depends(get_db_session),
) -> None:
    """Delete a favorite."""
    stmt = delete(Favorite).where(Favorite.id == favorite_id)
    result = await db.execute(stmt)
    await db.commit()

    if result.rowcount == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Favorite with id {favorite_id} not found",
        )


@router.delete("/by-item/{item_type}/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_favorite_by_item(
    item_type: str,
    item_id: UUID,
    db: AsyncSession = Depends(get_db_session),
) -> None:
    """Delete a favorite by item type and ID."""
    stmt = delete(Favorite).where(
        Favorite.item_type == item_type,
        Favorite.item_id == item_id
    )
    result = await db.execute(stmt)
    await db.commit()

    if result.rowcount == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Favorite for {item_type} with id {item_id} not found",
        )