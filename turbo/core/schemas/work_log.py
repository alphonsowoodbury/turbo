"""Work Log Pydantic schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class WorkLogBase(BaseModel):
    """Base work log schema with common fields."""

    started_by: str = Field(..., min_length=1, max_length=50)
    worktree_path: str | None = Field(None, max_length=500)
    branch_name: str | None = Field(None, max_length=100)
    commit_url: str | None = Field(None, max_length=500)

    @field_validator("started_by")
    @classmethod
    def validate_started_by(cls, v: str) -> str:
        """Validate started_by field."""
        valid_prefixes = ["user", "ai:context", "ai:turbo"]
        if not any(v.startswith(prefix) for prefix in valid_prefixes):
            raise ValueError(f"started_by must be one of: {', '.join(valid_prefixes)}")
        return v


class WorkLogCreate(WorkLogBase):
    """Schema for creating new work logs."""

    issue_id: UUID
    started_at: datetime | None = None  # Defaults to now if not provided


class WorkLogUpdate(BaseModel):
    """Schema for updating work logs (all fields optional)."""

    ended_at: datetime | None = None
    commit_url: str | None = Field(None, max_length=500)

    @field_validator("commit_url")
    @classmethod
    def validate_commit_url(cls, v: str | None) -> str | None:
        """Validate commit URL."""
        if v is not None and not v.strip():
            raise ValueError("Commit URL cannot be empty or whitespace")
        return v.strip() if v else v


class WorkLogResponse(WorkLogBase):
    """Schema for work log API responses."""

    id: UUID
    issue_id: UUID
    started_at: datetime
    ended_at: datetime | None
    created_at: datetime
    updated_at: datetime
    time_spent_seconds: int | None
    time_spent_minutes: int | None
    is_active: bool

    model_config = ConfigDict(from_attributes=True)
