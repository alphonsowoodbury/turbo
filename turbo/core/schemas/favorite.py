"""Favorite Pydantic schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class FavoriteBase(BaseModel):
    """Base favorite schema with common fields."""

    item_type: str = Field(..., pattern="^(issue|document|tag|blueprint|project)$")
    item_id: UUID


class FavoriteCreate(FavoriteBase):
    """Schema for creating new favorites."""

    pass


class FavoriteResponse(FavoriteBase):
    """Schema for favorite API responses."""

    id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class FavoriteWithDetails(FavoriteResponse):
    """Favorite with details about the favorited item."""

    item_title: str | None = None
    item_status: str | None = None

    model_config = ConfigDict(from_attributes=True)