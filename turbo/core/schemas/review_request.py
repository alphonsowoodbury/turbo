"""Review Request Pydantic schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ReviewRequestBase(BaseModel):
    """Base review request schema with common fields."""

    staff_id: UUID
    entity_type: str = Field(
        ..., pattern="^(issue|initiative|milestone|project|document)$"
    )
    entity_id: UUID
    request_type: str = Field(
        ..., pattern="^(scope_validation|feedback|approval|architecture_review|security_review|product_review)$"
    )
    description: str = Field(..., min_length=1)

    @field_validator("description")
    @classmethod
    def validate_description(cls, v: str) -> str:
        """Validate description."""
        if not v.strip():
            raise ValueError("Description cannot be empty or whitespace")
        return v.strip()


class ReviewRequestCreate(ReviewRequestBase):
    """Schema for creating new review requests."""

    status: str = Field(default="pending", pattern="^(pending|reviewed|dismissed)$")


class ReviewRequestUpdate(BaseModel):
    """Schema for updating review requests (all fields optional)."""

    status: str | None = Field(None, pattern="^(pending|reviewed|dismissed)$")
    description: str | None = Field(None, min_length=1)

    @field_validator("description")
    @classmethod
    def validate_description(cls, v: str | None) -> str | None:
        """Validate description."""
        if v is not None and not v.strip():
            raise ValueError("Description cannot be empty or whitespace")
        return v.strip() if v else v


class ReviewRequestResponse(ReviewRequestBase):
    """Schema for review request API responses."""

    id: UUID
    status: str
    reviewed_at: datetime | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ReviewRequestSummary(BaseModel):
    """Summary information about a review request."""

    id: UUID
    staff_id: UUID
    entity_type: str
    entity_id: UUID
    request_type: str
    status: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ReviewRequestWithStaff(ReviewRequestResponse):
    """Review request with staff information included."""

    staff_handle: str
    staff_name: str

    model_config = ConfigDict(from_attributes=True)


class ReviewRequestWithEntity(ReviewRequestResponse):
    """Review request with entity information included."""

    entity_title: str  # Title/name of the entity being reviewed

    model_config = ConfigDict(from_attributes=True)
