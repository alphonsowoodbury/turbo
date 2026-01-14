"""Decision schemas for API request/response models."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class OptionConsidered(BaseModel):
    """Schema for an option that was considered."""

    name: str
    description: str | None = None
    pros: list[str] = Field(default_factory=list)
    cons: list[str] = Field(default_factory=list)
    rejected_reason: str | None = None


class DecisionBase(BaseModel):
    """Base schema for Decision with common fields."""

    title: str = Field(..., min_length=1, max_length=200, description="Decision title")
    summary: str = Field(..., min_length=1, description="Brief description of what was decided")
    rationale: str = Field(..., min_length=1, description="Why this decision was made")
    context: str | None = Field(None, description="Background that led to this decision")
    constraints: list[str] | None = Field(None, description="Constraints that influenced the decision")
    options_considered: list[OptionConsidered] | None = Field(
        None, description="Alternatives with pros/cons"
    )
    decision_type: str = Field(
        default="tactical",
        pattern="^(strategic|tactical|technical|product)$",
        description="Type of decision",
    )
    impact_areas: list[str] | None = Field(None, description="Areas/systems affected")
    decided_by: str | None = Field(None, description="Who made the decision")


class DecisionCreate(DecisionBase):
    """Schema for creating a new decision."""

    decision_key: str | None = None  # Can be generated or provided


class DecisionUpdate(BaseModel):
    """Schema for updating a decision."""

    title: str | None = Field(None, min_length=1, max_length=200)
    summary: str | None = Field(None, min_length=1)
    rationale: str | None = Field(None, min_length=1)
    context: str | None = None
    constraints: list[str] | None = None
    options_considered: list[OptionConsidered] | None = None
    decision_type: str | None = Field(
        None, pattern="^(strategic|tactical|technical|product)$"
    )
    status: str | None = Field(
        None, pattern="^(proposed|approved|implemented|superseded|rejected)$"
    )
    impact_areas: list[str] | None = None
    decided_by: str | None = None
    superseded_by_id: UUID | None = None


class DecisionApprove(BaseModel):
    """Schema for approving a decision."""

    decided_by: str | None = None


class DecisionResponse(DecisionBase):
    """Schema for decision responses."""

    id: UUID
    decision_key: str | None
    status: str
    decided_at: datetime | None
    superseded_at: datetime | None
    superseded_by_id: UUID | None
    created_at: datetime
    updated_at: datetime
    initiative_count: int = Field(default=0, description="Number of spawned initiatives")

    model_config = {"from_attributes": True}


class DecisionList(BaseModel):
    """Schema for paginated decision list."""

    items: list[DecisionResponse]
    total: int
    page: int
    per_page: int
