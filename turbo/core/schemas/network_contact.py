"""NetworkContact Pydantic schemas for career management."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class NetworkContactBase(BaseModel):
    """Base network contact schema with common fields."""

    company_id: UUID | None = Field(default=None, description="Company where contact works (optional)")

    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    email: EmailStr | None = Field(default=None)
    linkedin_url: str | None = Field(default=None, max_length=500)
    phone: str | None = Field(default=None, max_length=50)

    current_title: str | None = Field(default=None, max_length=255)
    current_company: str | None = Field(default=None, max_length=255)

    contact_type: str | None = Field(
        default=None,
        pattern="^(recruiter_internal|recruiter_external|hiring_manager|peer|referrer|mentor|former_colleague)$"
    )

    relationship_strength: str = Field(
        default="cold",
        pattern="^(cold|warm|hot)$"
    )
    last_contact_date: datetime | None = Field(default=None)
    next_followup_date: datetime | None = Field(default=None)

    how_we_met: str | None = Field(default=None)
    conversation_history: str | None = Field(default=None)
    referral_status: str | None = Field(
        default=None,
        pattern="^(none|requested|agreed|completed)$"
    )

    github_url: str | None = Field(default=None, max_length=500)
    personal_website: str | None = Field(default=None, max_length=500)
    twitter_url: str | None = Field(default=None, max_length=500)

    notes: str | None = Field(default=None)
    is_active: bool = Field(default=True)

    @field_validator("first_name", "last_name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate name fields."""
        if not v.strip():
            raise ValueError("Name cannot be empty or whitespace")
        return v.strip()


class NetworkContactCreate(NetworkContactBase):
    """Schema for creating new network contacts."""

    tag_ids: list[UUID] | None = Field(default=None, description="List of tag IDs to associate with contact")


class NetworkContactUpdate(BaseModel):
    """Schema for updating network contacts (all fields optional)."""

    company_id: UUID | None = None

    first_name: str | None = Field(None, min_length=1, max_length=100)
    last_name: str | None = Field(None, min_length=1, max_length=100)
    email: EmailStr | None = None
    linkedin_url: str | None = Field(None, max_length=500)
    phone: str | None = Field(None, max_length=50)

    current_title: str | None = Field(None, max_length=255)
    current_company: str | None = Field(None, max_length=255)

    contact_type: str | None = Field(
        None,
        pattern="^(recruiter_internal|recruiter_external|hiring_manager|peer|referrer|mentor|former_colleague)$"
    )

    relationship_strength: str | None = Field(
        None,
        pattern="^(cold|warm|hot)$"
    )
    last_contact_date: datetime | None = None
    next_followup_date: datetime | None = None

    how_we_met: str | None = None
    conversation_history: str | None = None
    referral_status: str | None = Field(
        None,
        pattern="^(none|requested|agreed|completed)$"
    )

    github_url: str | None = Field(None, max_length=500)
    personal_website: str | None = Field(None, max_length=500)
    twitter_url: str | None = Field(None, max_length=500)

    notes: str | None = None
    is_active: bool | None = None
    tag_ids: list[UUID] | None = Field(None, description="List of tag IDs to associate with contact")

    @field_validator("first_name", "last_name")
    @classmethod
    def validate_name(cls, v: str | None) -> str | None:
        """Validate name fields."""
        if v is not None and not v.strip():
            raise ValueError("Name cannot be empty or whitespace")
        return v.strip() if v else v


class NetworkContactResponse(NetworkContactBase):
    """Schema for network contact API responses."""

    id: UUID
    interaction_count: int
    created_at: datetime
    updated_at: datetime

    # Relationship counts
    tag_count: int = 0

    model_config = ConfigDict(from_attributes=True)


class NetworkContactSummary(BaseModel):
    """Summary information about a network contact."""

    id: UUID
    first_name: str
    last_name: str
    current_title: str | None
    current_company: str | None
    contact_type: str | None
    relationship_strength: str
    last_contact_date: datetime | None

    model_config = ConfigDict(from_attributes=True)
