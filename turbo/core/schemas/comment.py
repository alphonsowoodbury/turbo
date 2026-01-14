"""Comment Pydantic schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class CommentBase(BaseModel):
    """Base comment schema with common fields."""

    content: str = Field(..., min_length=1)
    author_name: str = Field(..., min_length=1, max_length=100)
    author_type: str = Field(
        default="user", pattern="^(user|ai)$"
    )  # 'user' or 'ai'

    @field_validator("content")
    @classmethod
    def validate_content(cls, v: str) -> str:
        """Validate comment content."""
        if not v.strip():
            raise ValueError("Content cannot be empty or whitespace")
        return v.strip()

    @field_validator("author_name")
    @classmethod
    def validate_author_name(cls, v: str) -> str:
        """Validate author name."""
        if not v.strip():
            raise ValueError("Author name cannot be empty or whitespace")
        return v.strip()


class CommentCreate(CommentBase):
    """Schema for creating new comments."""

    entity_type: str = Field(..., pattern="^(issue|project|milestone|initiative|document|literature|blueprint)$")
    entity_id: UUID

    @field_validator("entity_type")
    @classmethod
    def validate_entity_type(cls, v: str) -> str:
        """Validate entity type."""
        valid_types = ["issue", "project", "milestone", "initiative", "document", "literature", "blueprint"]
        if v not in valid_types:
            raise ValueError(f"Entity type must be one of: {', '.join(valid_types)}")
        return v


class CommentUpdate(BaseModel):
    """Schema for updating comments (all fields optional)."""

    content: str | None = Field(None, min_length=1)

    @field_validator("content")
    @classmethod
    def validate_content(cls, v: str | None) -> str | None:
        """Validate comment content."""
        if v is not None and not v.strip():
            raise ValueError("Content cannot be empty or whitespace")
        return v.strip() if v else v


class CommentResponse(CommentBase):
    """Schema for comment API responses."""

    id: UUID
    entity_type: str
    entity_id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
