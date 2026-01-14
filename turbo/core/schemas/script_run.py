"""Script Run Pydantic schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ScriptRunCreate(BaseModel):
    """Schema for creating a new script run."""

    script_name: str = Field(..., min_length=1, max_length=255)
    script_path: str = Field(..., min_length=1, max_length=500)
    command: str | None = None
    arguments: str | None = None
    triggered_by: str | None = Field(None, max_length=100)


class ScriptRunUpdate(BaseModel):
    """Schema for updating a script run."""

    status: str | None = Field(None, pattern="^(running|completed|failed|cancelled)$")
    exit_code: int | None = None
    output: str | None = None
    error: str | None = None
    duration_seconds: float | None = Field(None, ge=0)
    files_processed: int | None = Field(None, ge=0)
    records_affected: int | None = Field(None, ge=0)


class ScriptRunResponse(BaseModel):
    """Schema for script run API responses."""

    id: UUID
    script_name: str
    script_path: str
    command: str | None
    arguments: str | None
    status: str
    exit_code: int | None
    output: str | None
    error: str | None
    duration_seconds: float
    files_processed: int
    records_affected: int
    triggered_by: str | None
    started_at: datetime
    completed_at: datetime | None
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ScriptRunSummary(BaseModel):
    """Summary information about a script run."""

    id: UUID
    script_name: str
    status: str
    duration_seconds: float
    started_at: datetime
    completed_at: datetime | None

    model_config = ConfigDict(from_attributes=True)
