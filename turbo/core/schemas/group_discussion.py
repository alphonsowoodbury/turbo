"""Group discussion Pydantic schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class GroupDiscussionBase(BaseModel):
    """Base group discussion schema with common fields."""

    name: str = Field(..., min_length=1, max_length=200)
    description: str | None = None
    discussion_type: str = Field(default="all_hands", pattern="^(all_hands|department|ad_hoc)$")
    participant_ids: list[UUID] = Field(default_factory=list)
    status: str = Field(default="active", pattern="^(active|archived)$")
    settings: dict = Field(
        default_factory=lambda: {
            "auto_summarize": True,
            "allow_user_participation": True,
            "max_messages": None,
        }
    )

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate discussion name."""
        if not v.strip():
            raise ValueError("Name cannot be empty or whitespace")
        return v.strip()


class GroupDiscussionCreate(GroupDiscussionBase):
    """Schema for creating new group discussion."""
    pass


class GroupDiscussionUpdate(BaseModel):
    """Schema for updating group discussion (all fields optional)."""

    name: str | None = Field(None, min_length=1, max_length=200)
    description: str | None = None
    discussion_type: str | None = Field(None, pattern="^(all_hands|department|ad_hoc)$")
    participant_ids: list[UUID] | None = None
    status: str | None = Field(None, pattern="^(active|archived)$")
    settings: dict | None = None

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str | None) -> str | None:
        """Validate discussion name."""
        if v is not None and not v.strip():
            raise ValueError("Name cannot be empty or whitespace")
        return v.strip() if v else v


class GroupDiscussionResponse(GroupDiscussionBase):
    """Schema for group discussion API responses."""

    id: UUID
    message_count: int
    last_activity_at: datetime | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class GroupDiscussionSummary(BaseModel):
    """Summary information about a group discussion."""

    id: UUID
    name: str
    discussion_type: str
    participant_count: int
    message_count: int
    status: str
    last_activity_at: datetime | None

    model_config = ConfigDict(from_attributes=True)

    @property
    def participant_count(self) -> int:
        """Get number of participants."""
        return len(self.participant_ids) if hasattr(self, 'participant_ids') else 0
