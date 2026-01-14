"""Staff Pydantic schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class StaffBase(BaseModel):
    """Base staff schema with common fields."""

    handle: str = Field(..., min_length=1, max_length=50, pattern="^[a-zA-Z0-9_]+$")
    alias: str | None = Field(None, min_length=1, max_length=20, pattern="^[a-zA-Z0-9_]+$")
    name: str = Field(..., min_length=1, max_length=200)
    description: str = Field(..., min_length=1, max_length=1000)
    persona: str = Field(..., min_length=1)
    role_type: str = Field(
        ..., pattern="^(leadership|domain_expert)$"
    )
    role_title: str | None = Field(None, min_length=1, max_length=100)
    is_leadership_role: bool = Field(default=False)
    monitoring_scope: dict = Field(
        default_factory=lambda: {
            "entity_types": [],
            "tags": [],
            "focus": "",
            "metrics": []
        }
    )
    capabilities: list[str] = Field(default_factory=list)
    allowed_tools: list[str] = Field(
        default_factory=lambda: ["list_projects", "get_project", "create_document"]
    )
    is_active: bool = Field(default=True)
    overall_rating: float | None = Field(default=None, ge=0.0, le=5.0)
    performance_metrics: dict = Field(
        default_factory=lambda: {
            "completed_tasks": 0,
            "avg_response_time_hours": 0.0,
            "quality_score": 0.0,
            "completion_rate": 0.0,
            "total_assignments": 0,
        }
    )

    @field_validator("handle")
    @classmethod
    def validate_handle(cls, v: str) -> str:
        """Validate staff handle."""
        if not v.strip():
            raise ValueError("Handle cannot be empty or whitespace")
        # Ensure handle doesn't start with @ (we add that in display)
        if v.startswith("@"):
            raise ValueError("Handle should not start with @ symbol")
        return v.strip()

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate staff name."""
        if not v.strip():
            raise ValueError("Name cannot be empty or whitespace")
        return v.strip()

    @field_validator("description")
    @classmethod
    def validate_description(cls, v: str) -> str:
        """Validate staff description."""
        if not v.strip():
            raise ValueError("Description cannot be empty or whitespace")
        return v.strip()

    @field_validator("persona")
    @classmethod
    def validate_persona(cls, v: str) -> str:
        """Validate staff persona."""
        if not v.strip():
            raise ValueError("Persona cannot be empty or whitespace")
        return v.strip()


class StaffCreate(StaffBase):
    """Schema for creating new staff."""
    pass


class StaffUpdate(BaseModel):
    """Schema for updating staff (all fields optional)."""

    handle: str | None = Field(None, min_length=1, max_length=50, pattern="^[a-zA-Z0-9_]+$")
    alias: str | None = Field(None, min_length=1, max_length=20, pattern="^[a-zA-Z0-9_]+$")
    name: str | None = Field(None, min_length=1, max_length=200)
    description: str | None = Field(None, min_length=1, max_length=1000)
    persona: str | None = Field(None, min_length=1)
    role_type: str | None = Field(None, pattern="^(leadership|domain_expert)$")
    role_title: str | None = Field(None, min_length=1, max_length=100)
    is_leadership_role: bool | None = None
    monitoring_scope: dict | None = None
    capabilities: list[str] | None = None
    allowed_tools: list[str] | None = None
    is_active: bool | None = None
    overall_rating: float | None = Field(default=None, ge=0.0, le=5.0)
    performance_metrics: dict | None = None

    @field_validator("handle")
    @classmethod
    def validate_handle(cls, v: str | None) -> str | None:
        """Validate staff handle."""
        if v is not None:
            if not v.strip():
                raise ValueError("Handle cannot be empty or whitespace")
            if v.startswith("@"):
                raise ValueError("Handle should not start with @ symbol")
            return v.strip()
        return v

    @field_validator("name", "description", "persona")
    @classmethod
    def validate_text_fields(cls, v: str | None) -> str | None:
        """Validate text fields."""
        if v is not None and not v.strip():
            raise ValueError("Field cannot be empty or whitespace")
        return v.strip() if v else v


class StaffResponse(StaffBase):
    """Schema for staff API responses."""

    id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class StaffSummary(BaseModel):
    """Summary information about a staff member."""

    id: UUID
    handle: str
    alias: str | None
    name: str
    role_type: str
    role_title: str | None
    is_leadership_role: bool
    is_active: bool

    model_config = ConfigDict(from_attributes=True)


class StaffConversationMessage(BaseModel):
    """Schema for staff conversation messages."""

    staff_id: UUID
    message_type: str = Field(..., pattern="^(user|assistant)$")
    content: str = Field(..., min_length=1)
    is_group_discussion: bool = Field(default=False)
    group_discussion_id: UUID | None = None

    @field_validator("content")
    @classmethod
    def validate_content(cls, v: str) -> str:
        """Validate message content."""
        if not v.strip():
            raise ValueError("Content cannot be empty or whitespace")
        return v.strip()


class StaffConversationResponse(BaseModel):
    """Schema for staff conversation API responses."""

    id: UUID
    staff_id: UUID | None  # None for user messages in group discussions
    message_type: str
    content: str
    is_group_discussion: bool
    group_discussion_id: UUID | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class StaffActivityItem(BaseModel):
    """Activity feed item for staff profile."""

    id: UUID
    activity_type: str  # message, comment, review_request, assignment
    title: str
    description: str | None
    entity_type: str | None  # issue, project, etc.
    entity_id: UUID | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class StaffProfileResponse(BaseModel):
    """Comprehensive staff profile with analytics."""

    # Basic info
    staff: StaffResponse

    # Work assignments
    assigned_review_requests: list[dict]
    assigned_issues_count: int
    pending_approvals_count: int

    # Performance metrics (computed)
    computed_metrics: dict = Field(
        default_factory=lambda: {
            "response_rate": 0.0,  # percentage
            "avg_completion_time_hours": 0.0,
            "active_conversations": 0,
            "total_messages": 0,
        }
    )

    # Recent activity
    recent_activity: list[StaffActivityItem] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)
