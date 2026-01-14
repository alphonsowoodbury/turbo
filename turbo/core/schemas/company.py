"""Company Pydantic schemas for career management."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class CompanyBase(BaseModel):
    """Base company schema with common fields."""

    name: str = Field(..., min_length=1, max_length=255)
    website: str | None = Field(default=None, max_length=500)
    industry: str | None = Field(default=None, max_length=100)
    size: str | None = Field(default=None, max_length=50)  # e.g., "Startup (< 50)", "Medium (50-500)", "Large (500+)"
    location: str | None = Field(default=None, max_length=255)
    remote_policy: str | None = Field(default=None, max_length=50)  # e.g., "Remote", "Hybrid", "In-Office"

    target_status: str = Field(
        default="researching",
        pattern="^(researching|interested|applied|interviewing|offer|accepted|rejected|not_interested)$"
    )

    research_notes: str | None = Field(default=None)
    culture_notes: str | None = Field(default=None)
    tech_stack: dict | None = Field(default=None, description="JSONB field for tech stack information")
    glassdoor_rating: float | None = Field(default=None, ge=0.0, le=5.0)

    linkedin_url: str | None = Field(default=None, max_length=500)
    careers_page_url: str | None = Field(default=None, max_length=500)

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate company name."""
        if not v.strip():
            raise ValueError("Name cannot be empty or whitespace")
        return v.strip()


class CompanyCreate(CompanyBase):
    """Schema for creating new companies."""

    tag_ids: list[UUID] | None = Field(default=None, description="List of tag IDs to associate with company")


class CompanyUpdate(BaseModel):
    """Schema for updating companies (all fields optional)."""

    name: str | None = Field(None, min_length=1, max_length=255)
    website: str | None = Field(None, max_length=500)
    industry: str | None = Field(None, max_length=100)
    size: str | None = Field(None, max_length=50)
    location: str | None = Field(None, max_length=255)
    remote_policy: str | None = Field(None, max_length=50)
    target_status: str | None = Field(
        None,
        pattern="^(researching|interested|applied|interviewing|offer|accepted|rejected|not_interested)$"
    )
    research_notes: str | None = None
    culture_notes: str | None = None
    tech_stack: dict | None = None
    glassdoor_rating: float | None = Field(None, ge=0.0, le=5.0)
    linkedin_url: str | None = Field(None, max_length=500)
    careers_page_url: str | None = Field(None, max_length=500)
    tag_ids: list[UUID] | None = Field(None, description="List of tag IDs to associate with company")

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str | None) -> str | None:
        """Validate company name."""
        if v is not None and not v.strip():
            raise ValueError("Name cannot be empty or whitespace")
        return v.strip() if v else v


class CompanyResponse(CompanyBase):
    """Schema for company API responses."""

    id: UUID
    application_count: int
    created_at: datetime
    updated_at: datetime

    # Relationship counts
    tag_count: int = 0
    contact_count: int = 0

    model_config = ConfigDict(from_attributes=True)


class CompanySummary(BaseModel):
    """Summary information about a company."""

    id: UUID
    name: str
    industry: str | None
    target_status: str
    application_count: int
    contact_count: int

    model_config = ConfigDict(from_attributes=True)
