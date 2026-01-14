"""JobApplication Pydantic schemas for career management."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class JobApplicationBase(BaseModel):
    """Base job application schema with common fields."""

    company_id: UUID | None = Field(default=None, description="Company this application is for")
    resume_id: UUID | None = Field(default=None, description="Resume version used for this application")
    project_id: UUID | None = Field(default=None, description="Optional portfolio project showcased")
    cover_letter_id: UUID | None = Field(default=None, description="Cover letter document used")
    referrer_contact_id: UUID | None = Field(default=None, description="Contact who provided referral")

    job_title: str = Field(..., min_length=1, max_length=255)
    job_description: str | None = Field(default=None)
    job_url: str | None = Field(default=None, max_length=500)
    salary_min: int | None = Field(default=None, ge=0)
    salary_max: int | None = Field(default=None, ge=0)
    location: str | None = Field(default=None, max_length=255)
    remote_policy: str | None = Field(default=None, max_length=50)

    status: str = Field(
        default="researching",
        pattern="^(researching|interested|applied|screening|phone_screen|technical_interview|onsite|offer|negotiating|accepted|rejected|withdrawn|ghosted)$"
    )
    application_date: datetime | None = Field(default=None)
    last_contact_date: datetime | None = Field(default=None)
    next_followup_date: datetime | None = Field(default=None)

    resume_version: str | None = Field(default=None, max_length=50)
    source: str | None = Field(default=None, max_length=100)  # LinkedIn, Indeed, Referral, etc.

    interview_notes: str | None = Field(default=None)
    rejection_reason: str | None = Field(default=None)
    notes: str | None = Field(default=None)

    @field_validator("job_title")
    @classmethod
    def validate_job_title(cls, v: str) -> str:
        """Validate job title."""
        if not v.strip():
            raise ValueError("Job title cannot be empty or whitespace")
        return v.strip()

    @field_validator("salary_max")
    @classmethod
    def validate_salary_range(cls, v: int | None, info) -> int | None:
        """Validate salary max is greater than min."""
        if v is not None and info.data.get("salary_min") is not None:
            if v < info.data["salary_min"]:
                raise ValueError("salary_max must be greater than or equal to salary_min")
        return v


class JobApplicationCreate(JobApplicationBase):
    """Schema for creating new job applications."""

    tag_ids: list[UUID] | None = Field(default=None, description="List of tag IDs to associate with application")


class JobApplicationUpdate(BaseModel):
    """Schema for updating job applications (all fields optional)."""

    company_id: UUID | None = None
    resume_id: UUID | None = None
    project_id: UUID | None = None
    cover_letter_id: UUID | None = None
    referrer_contact_id: UUID | None = None

    job_title: str | None = Field(None, min_length=1, max_length=255)
    job_description: str | None = None
    job_url: str | None = Field(None, max_length=500)
    salary_min: int | None = Field(None, ge=0)
    salary_max: int | None = Field(None, ge=0)
    location: str | None = Field(None, max_length=255)
    remote_policy: str | None = Field(None, max_length=50)

    status: str | None = Field(
        None,
        pattern="^(researching|interested|applied|screening|phone_screen|technical_interview|onsite|offer|negotiating|accepted|rejected|withdrawn|ghosted)$"
    )
    application_date: datetime | None = None
    last_contact_date: datetime | None = None
    next_followup_date: datetime | None = None

    resume_version: str | None = Field(None, max_length=50)
    source: str | None = Field(None, max_length=100)

    interview_notes: str | None = None
    rejection_reason: str | None = None
    notes: str | None = None
    tag_ids: list[UUID] | None = Field(None, description="List of tag IDs to associate with application")

    @field_validator("job_title")
    @classmethod
    def validate_job_title(cls, v: str | None) -> str | None:
        """Validate job title."""
        if v is not None and not v.strip():
            raise ValueError("Job title cannot be empty or whitespace")
        return v.strip() if v else v

    @field_validator("salary_max")
    @classmethod
    def validate_salary_range(cls, v: int | None, info) -> int | None:
        """Validate salary max is greater than min."""
        if v is not None and info.data.get("salary_min") is not None:
            if v < info.data["salary_min"]:
                raise ValueError("salary_max must be greater than or equal to salary_min")
        return v


class JobApplicationResponse(JobApplicationBase):
    """Schema for job application API responses."""

    id: UUID
    interview_count: int
    response_time_hours: int | None
    created_at: datetime
    updated_at: datetime

    # Relationship counts
    tag_count: int = 0

    model_config = ConfigDict(from_attributes=True)


class JobApplicationSummary(BaseModel):
    """Summary information about a job application."""

    id: UUID
    job_title: str
    company_id: UUID | None
    status: str
    application_date: datetime | None
    next_followup_date: datetime | None
    interview_count: int

    model_config = ConfigDict(from_attributes=True)
