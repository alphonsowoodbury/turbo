"""Project Pydantic schemas."""

import re
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ProjectBase(BaseModel):
    """Base project schema with common fields."""

    name: str = Field(..., min_length=1, max_length=100)
    description: str = Field(..., min_length=1)
    priority: str = Field(default="medium", pattern="^(low|medium|high|critical)$")
    status: str = Field(
        default="active", pattern="^(active|on_hold|completed|archived)$"
    )
    completion_percentage: float | None = Field(default=0.0, ge=0.0, le=100.0)
    repository_path: str | None = Field(default=None, max_length=500, description="Local filesystem path to git repository")
    workspace: str = Field(default="personal", pattern="^(personal|freelance|work)$")
    work_company: str | None = Field(default=None, max_length=100)
    assigned_to_type: str | None = Field(
        default=None, pattern="^(user|staff)$", description="Owner type: user or staff"
    )
    assigned_to_id: UUID | None = Field(
        default=None, description="UUID of the assigned user or staff member"
    )

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate project name."""
        if not v.strip():
            raise ValueError("Name cannot be empty or whitespace")
        return v.strip()

    @field_validator("description")
    @classmethod
    def validate_description(cls, v: str) -> str:
        """Validate project description."""
        if not v.strip():
            raise ValueError("Description cannot be empty or whitespace")
        return v.strip()


class ProjectCreate(ProjectBase):
    """Schema for creating new projects."""

    project_key: str = Field(..., min_length=2, max_length=10, description="Unique project key (e.g., CNTXT, TURBO)")
    is_archived: bool | None = Field(default=False)

    @field_validator("project_key")
    @classmethod
    def validate_project_key(cls, v: str) -> str:
        """Validate project key format."""
        if not v:
            raise ValueError("Project key is required")

        v = v.strip().upper()

        if len(v) < 2 or len(v) > 10:
            raise ValueError("Project key must be 2-10 characters")

        if not re.match(r"^[A-Z][A-Z0-9]*$", v):
            raise ValueError("Project key must start with a letter and contain only uppercase letters and numbers")

        return v


class ProjectUpdate(BaseModel):
    """Schema for updating projects (all fields optional)."""

    name: str | None = Field(None, min_length=1, max_length=100)
    description: str | None = Field(None, min_length=1)
    priority: str | None = Field(None, pattern="^(low|medium|high|critical)$")
    status: str | None = Field(None, pattern="^(active|on_hold|completed|archived)$")
    completion_percentage: float | None = Field(None, ge=0.0, le=100.0)
    is_archived: bool | None = None
    repository_path: str | None = Field(None, max_length=500)
    workspace: str | None = Field(None, pattern="^(personal|freelance|work)$")
    work_company: str | None = Field(None, max_length=100)
    assigned_to_type: str | None = Field(None, pattern="^(user|staff)$")
    assigned_to_id: UUID | None = None

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str | None) -> str | None:
        """Validate project name."""
        if v is not None and not v.strip():
            raise ValueError("Name cannot be empty or whitespace")
        return v.strip() if v else v

    @field_validator("description")
    @classmethod
    def validate_description(cls, v: str | None) -> str | None:
        """Validate project description."""
        if v is not None and not v.strip():
            raise ValueError("Description cannot be empty or whitespace")
        return v.strip() if v else v


class ProjectResponse(ProjectBase):
    """Schema for project API responses."""

    id: UUID
    project_key: str
    is_archived: bool
    repository_path: str | None
    workspace: str
    work_company: str | None
    assigned_to_type: str | None
    assigned_to_id: UUID | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ProjectWithStats(ProjectResponse):
    """Project response with additional statistics."""

    total_issues: int = 0
    open_issues: int = 0
    closed_issues: int = 0
    completion_rate: float = 0.0


class ProjectSummary(BaseModel):
    """Summary information about a project."""

    id: UUID
    project_key: str
    name: str
    status: str
    priority: str
    completion_percentage: float
    total_issues: int

    model_config = ConfigDict(from_attributes=True)
