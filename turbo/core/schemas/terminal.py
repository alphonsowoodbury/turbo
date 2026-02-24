"""Pydantic schemas for terminal sessions."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class TerminalSessionCreate(BaseModel):
    """Schema for creating a terminal session."""

    user_id: str = Field(..., description="User ID owning the session")
    project_id: UUID | None = Field(None, description="Optional project context")
    issue_id: UUID | None = Field(None, description="Optional issue context")
    shell: str = Field("/bin/bash", description="Shell to use")
    working_directory: str = Field("~/", description="Initial working directory")
    environment_vars: dict[str, str] | None = Field(
        None, description="Additional environment variables"
    )


class TerminalSessionResponse(BaseModel):
    """Schema for terminal session response."""

    id: UUID
    user_id: str
    session_id: str
    project_id: UUID | None = None
    issue_id: UUID | None = None
    shell: str
    working_directory: str
    environment_vars: dict[str, str] | None = None
    pid: int | None = None
    is_active: bool
    last_activity: datetime
    created_at: datetime
    ended_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class TerminalSessionUpdate(BaseModel):
    """Schema for updating a terminal session."""

    is_active: bool | None = None
    last_activity: datetime | None = None
    ended_at: datetime | None = None


class TerminalInput(BaseModel):
    """Schema for terminal input."""

    session_id: str = Field(..., description="Terminal session ID")
    data: str = Field(..., description="Input data to send to terminal")


class TerminalOutput(BaseModel):
    """Schema for terminal output."""

    session_id: str
    data: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class TerminalResize(BaseModel):
    """Schema for terminal resize events."""

    session_id: str
    rows: int = Field(..., ge=1, le=500)
    cols: int = Field(..., ge=1, le=500)
