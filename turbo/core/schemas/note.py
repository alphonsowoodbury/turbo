"""Note Pydantic schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class TagSummary(BaseModel):
    """Summary of a tag."""

    id: UUID
    name: str
    color: str

    model_config = ConfigDict(from_attributes=True)


class NoteBase(BaseModel):
    """Base note schema with common fields."""

    title: str = Field(..., min_length=1, max_length=500)
    content: str | None = None
    workspace: str = Field(default="personal", pattern="^(personal|freelance|work)$")
    work_company: str | None = Field(None, max_length=100)

    @field_validator("title")
    @classmethod
    def validate_title(cls, v: str) -> str:
        """Validate note title."""
        if not v.strip():
            raise ValueError("Title cannot be empty or whitespace")
        return v.strip()

    @field_validator("content")
    @classmethod
    def validate_content(cls, v: str | None) -> str | None:
        """Validate note content."""
        if v is not None:
            return v.strip() if v.strip() else None
        return v


class NoteCreate(NoteBase):
    """Schema for creating new notes."""

    tag_ids: list[UUID] | None = Field(default=None)


class NoteUpdate(BaseModel):
    """Schema for updating notes (all fields optional)."""

    title: str | None = Field(None, min_length=1, max_length=500)
    content: str | None = None
    workspace: str | None = Field(None, pattern="^(personal|freelance|work)$")
    work_company: str | None = Field(None, max_length=100)
    is_archived: bool | None = None
    tag_ids: list[UUID] | None = None

    @field_validator("title")
    @classmethod
    def validate_title(cls, v: str | None) -> str | None:
        """Validate note title."""
        if v is not None and not v.strip():
            raise ValueError("Title cannot be empty or whitespace")
        return v.strip() if v else v

    @field_validator("content")
    @classmethod
    def validate_content(cls, v: str | None) -> str | None:
        """Validate note content."""
        if v is not None:
            return v.strip() if v.strip() else None
        return v


class NoteResponse(NoteBase):
    """Schema for note API responses."""

    id: UUID
    is_archived: bool
    created_at: datetime
    updated_at: datetime
    tags: list[TagSummary] = []

    model_config = ConfigDict(from_attributes=True)


class NoteSummary(BaseModel):
    """Summary of a note for list views."""

    id: UUID
    title: str
    workspace: str
    is_archived: bool
    created_at: datetime
    tag_count: int = 0

    model_config = ConfigDict(from_attributes=True)
