"""Pydantic schemas for issue dependencies."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class IssueDependencyCreate(BaseModel):
    """Schema for creating an issue dependency."""

    blocking_issue_id: UUID = Field(..., description="ID of the issue that blocks")
    blocked_issue_id: UUID = Field(..., description="ID of the issue that is blocked")
    dependency_type: str = Field(
        default="blocks", description="Type of dependency relationship"
    )


class IssueDependencyResponse(BaseModel):
    """Schema for issue dependency response."""

    blocking_issue_id: UUID
    blocked_issue_id: UUID
    dependency_type: str
    created_at: datetime

    model_config = {"from_attributes": True}


class IssueDependencies(BaseModel):
    """Schema for all dependencies of an issue."""

    blocking: list[UUID] = Field(
        default_factory=list, description="Issues that block this issue"
    )
    blocked_by: list[UUID] = Field(
        default_factory=list, description="Issues blocked by this issue"
    )


class DependencyChain(BaseModel):
    """Schema for a dependency chain."""

    issue_id: UUID
    chain: list[UUID] = Field(
        default_factory=list,
        description="All issues that must be completed first, in order",
    )