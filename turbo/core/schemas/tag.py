"""Tag Pydantic schemas."""

from datetime import datetime
import re
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class TagBase(BaseModel):
    """Base tag schema with common fields."""

    name: str = Field(..., min_length=1, max_length=50)
    color: str = Field(..., pattern="^#[0-9A-Fa-f]{6}$")
    description: str | None = Field(None, max_length=200)

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate tag name."""
        if not v.strip():
            raise ValueError("Name cannot be empty or whitespace")
        return v.strip()

    @field_validator("color")
    @classmethod
    def validate_color(cls, v: str) -> str:
        """Validate hex color format."""
        if not re.match(r"^#[0-9A-Fa-f]{6}$", v):
            raise ValueError("Invalid hex color format. Must be #RRGGBB")
        return v.upper()


class TagCreate(TagBase):
    """Schema for creating new tags."""

    pass


class TagUpdate(BaseModel):
    """Schema for updating tags."""

    name: str | None = Field(None, min_length=1, max_length=50)
    color: str | None = Field(None, pattern="^#[0-9A-Fa-f]{6}$")
    description: str | None = Field(None, max_length=200)

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str | None) -> str | None:
        """Validate tag name."""
        if v is not None:
            if not v.strip():
                raise ValueError("Name cannot be empty or whitespace")
            return v.strip()
        return v

    @field_validator("color")
    @classmethod
    def validate_color(cls, v: str | None) -> str | None:
        """Validate hex color format."""
        if v is not None:
            if not re.match(r"^#[0-9A-Fa-f]{6}$", v):
                raise ValueError("Invalid hex color format. Must be #RRGGBB")
            return v.upper()
        return v


class TagResponse(TagBase):
    """Schema for tag API responses."""

    id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TagSummary(BaseModel):
    """Summary information about a tag."""

    id: UUID
    name: str
    color: str

    model_config = ConfigDict(from_attributes=True)
