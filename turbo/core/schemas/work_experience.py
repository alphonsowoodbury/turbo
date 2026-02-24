"""Work experience Pydantic schemas."""

from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


# ============================================================================
# Achievement Fact Schemas
# ============================================================================

class AchievementFactBase(BaseModel):
    """Base schema for achievement facts."""

    fact_text: str = Field(..., min_length=1, max_length=5000, description="Core factual statement")
    metric_type: str | None = Field(None, max_length=50, description="Type of metric (cost_savings, time_reduction, scale, etc.)")
    metric_value: float | None = Field(None, ge=0, description="Numerical value of the metric")
    metric_unit: str | None = Field(None, max_length=50, description="Unit of measurement (percentage, dollars, days, etc.)")
    dimensions: list[str] = Field(default_factory=list, description="Dimensional tags for extraction (leadership, technical, etc.)")
    leadership_principles: list[str] = Field(default_factory=list, description="Amazon Leadership Principles demonstrated")
    skills_used: list[str] = Field(default_factory=list, description="Skills demonstrated in this achievement")
    context: str | None = Field(None, max_length=2000, description="Situation/Task context for STAR format")
    impact: str | None = Field(None, max_length=2000, description="Result/Impact for STAR format")
    display_order: int = Field(default=0, ge=0, description="Display order within experience")


class AchievementFactCreate(AchievementFactBase):
    """Schema for creating an achievement fact."""

    experience_id: UUID = Field(..., description="Work experience this achievement belongs to")


class AchievementFactUpdate(BaseModel):
    """Schema for updating an achievement fact."""

    fact_text: str | None = Field(None, min_length=1, max_length=5000)
    metric_type: str | None = Field(None, max_length=50)
    metric_value: float | None = Field(None, ge=0)
    metric_unit: str | None = Field(None, max_length=50)
    dimensions: list[str] | None = None
    leadership_principles: list[str] | None = None
    skills_used: list[str] | None = None
    context: str | None = Field(None, max_length=2000)
    impact: str | None = Field(None, max_length=2000)
    display_order: int | None = Field(None, ge=0)


class AchievementFactInDB(AchievementFactBase):
    """Schema for achievement fact from database."""

    id: UUID
    experience_id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AchievementFactPublic(AchievementFactInDB):
    """Public schema for achievement fact responses."""

    pass


# ============================================================================
# Work Experience Schemas
# ============================================================================

class WorkExperienceBase(BaseModel):
    """Base schema for work experiences."""

    role_title: str = Field(..., min_length=1, max_length=255, description="Job title/role")
    start_date: date = Field(..., description="Start date of employment")
    end_date: date | None = Field(None, description="End date of employment (null if current)")
    is_current: bool = Field(default=False, description="Whether this is current employment")
    location: str | None = Field(None, max_length=255, description="Work location")
    employment_type: str | None = Field(None, description="Employment type (full_time, part_time, contract, freelance)")
    department: str | None = Field(None, max_length=100, description="Department/division")
    team_context: dict | None = Field(None, description="Team structure context (team_size, reporting_to, etc.)")
    technologies: list[str] | None = Field(None, description="Technologies/tools used")

    @field_validator("employment_type")
    @classmethod
    def validate_employment_type(cls, v: str | None) -> str | None:
        """Validate employment type."""
        if v is not None and v not in ["full_time", "part_time", "contract", "freelance"]:
            raise ValueError("employment_type must be one of: full_time, part_time, contract, freelance")
        return v

    @field_validator("end_date")
    @classmethod
    def validate_dates(cls, v: date | None, info) -> date | None:
        """Validate that end_date is after start_date."""
        if v is not None and "start_date" in info.data:
            start_date = info.data["start_date"]
            if v < start_date:
                raise ValueError("end_date must be on or after start_date")
        return v

    @field_validator("is_current")
    @classmethod
    def validate_current(cls, v: bool, info) -> bool:
        """Validate that current positions don't have end_date."""
        if v and "end_date" in info.data and info.data["end_date"] is not None:
            raise ValueError("Current positions (is_current=True) cannot have an end_date")
        return v


class WorkExperienceCreate(WorkExperienceBase):
    """Schema for creating a work experience."""

    company_id: UUID | None = Field(None, description="Company ID (optional)")


class WorkExperienceUpdate(BaseModel):
    """Schema for updating a work experience."""

    company_id: UUID | None = None
    role_title: str | None = Field(None, min_length=1, max_length=255)
    start_date: date | None = None
    end_date: date | None = None
    is_current: bool | None = None
    location: str | None = Field(None, max_length=255)
    employment_type: str | None = None
    department: str | None = Field(None, max_length=100)
    team_context: dict | None = None
    technologies: list[str] | None = None

    @field_validator("employment_type")
    @classmethod
    def validate_employment_type(cls, v: str | None) -> str | None:
        """Validate employment type."""
        if v is not None and v not in ["full_time", "part_time", "contract", "freelance"]:
            raise ValueError("employment_type must be one of: full_time, part_time, contract, freelance")
        return v


class WorkExperienceInDB(WorkExperienceBase):
    """Schema for work experience from database."""

    id: UUID
    company_id: UUID | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class WorkExperiencePublic(WorkExperienceInDB):
    """Public schema for work experience responses."""

    achievements: list[AchievementFactPublic] = Field(default_factory=list, description="Associated achievements")


class WorkExperienceWithCompany(WorkExperiencePublic):
    """Work experience with company details."""

    company_name: str | None = Field(None, description="Company name (if company_id is set)")


# ============================================================================
# Query/Filter Schemas
# ============================================================================

class WorkExperienceQuery(BaseModel):
    """Query parameters for listing work experiences."""

    company_id: UUID | None = Field(None, description="Filter by company")
    is_current: bool | None = Field(None, description="Filter by current employment")
    employment_type: str | None = Field(None, description="Filter by employment type")
    limit: int = Field(default=100, ge=1, le=500, description="Maximum number of results")
    offset: int = Field(default=0, ge=0, description="Number of results to skip")


class AchievementFactQuery(BaseModel):
    """Query parameters for listing achievement facts."""

    experience_id: UUID | None = Field(None, description="Filter by work experience")
    metric_type: str | None = Field(None, description="Filter by metric type")
    dimensions: list[str] | None = Field(None, description="Filter by dimensions (must contain all)")
    leadership_principles: list[str] | None = Field(None, description="Filter by leadership principles")
    skills_used: list[str] | None = Field(None, description="Filter by skills used")
    limit: int = Field(default=100, ge=1, le=500, description="Maximum number of results")
    offset: int = Field(default=0, ge=0, description="Number of results to skip")
