"""SavedFilter Pydantic schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class SavedFilterBase(BaseModel):
    """Base saved filter schema with common fields."""

    name: str = Field(..., min_length=1, max_length=100)
    description: str | None = Field(None, max_length=255)
    filter_config: str  # JSON string


class SavedFilterCreate(SavedFilterBase):
    """Schema for creating new saved filters."""

    project_id: UUID


class SavedFilterUpdate(BaseModel):
    """Schema for updating saved filters."""

    name: str | None = Field(None, min_length=1, max_length=100)
    description: str | None = Field(None, max_length=255)
    filter_config: str | None = None


class SavedFilterResponse(SavedFilterBase):
    """Schema for saved filter API responses."""

    id: UUID
    project_id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)