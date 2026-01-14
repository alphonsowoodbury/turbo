"""Mentor Pydantic schemas for validation and serialization."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class MentorBase(BaseModel):
    """Base schema for Mentor."""

    name: str = Field(..., max_length=200, description="Mentor name")
    description: str = Field(..., description="What this mentor specializes in")
    persona: str = Field(..., description="System prompt defining mentor personality and expertise")
    workspace: str = Field("personal", pattern="^(personal|freelance|work)$", description="Workspace context")
    work_company: str | None = Field(None, max_length=100, description="Company name for work workspace")
    context_preferences: dict = Field(
        default={
            "include_projects": True,
            "include_issues": True,
            "include_documents": True,
            "include_influencers": True,
            "max_items": 10,
        },
        description="Configuration for what context to include"
    )
    is_active: bool = Field(True, description="Whether mentor is active")

    @field_validator("workspace")
    @classmethod
    def validate_workspace(cls, v: str) -> str:
        """Validate workspace value."""
        if v not in ("personal", "freelance", "work"):
            raise ValueError("Workspace must be one of: personal, freelance, work")
        return v

    @field_validator("work_company")
    @classmethod
    def validate_work_company(cls, v: str | None, info) -> str | None:
        """Validate work_company is provided when workspace is work."""
        if info.data.get("workspace") == "work" and not v:
            raise ValueError("work_company is required when workspace is 'work'")
        return v


class MentorCreate(MentorBase):
    """Schema for creating a mentor."""

    pass


class MentorUpdate(BaseModel):
    """Schema for updating a mentor."""

    name: str | None = Field(None, max_length=200)
    description: str | None = None
    persona: str | None = None
    workspace: str | None = Field(None, pattern="^(personal|freelance|work)$")
    work_company: str | None = Field(None, max_length=100)
    context_preferences: dict | None = None
    is_active: bool | None = None


class MentorResponse(MentorBase):
    """Schema for mentor response."""

    id: UUID
    created_at: datetime
    updated_at: datetime
    message_count: int | None = Field(None, description="Number of messages in conversation")

    model_config = {"from_attributes": True}


class MentorListResponse(BaseModel):
    """Schema for list of mentors."""

    mentors: list[MentorResponse]
    total: int
