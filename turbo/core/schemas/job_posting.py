"""Pydantic schemas for job posting and search criteria."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict


# ============================================================================
# Job Posting Schemas
# ============================================================================

class JobPostingBase(BaseModel):
    """Base schema for job posting."""

    source: str = Field(..., max_length=100, description="Job board source")
    source_url: str = Field(..., description="Original job posting URL")
    application_url: str | None = Field(None, description="Direct application URL (company's application page)")
    external_id: str | None = Field(None, max_length=255, description="External platform job ID")

    company_id: UUID | None = None
    company_name: str = Field(..., max_length=255)

    job_title: str = Field(..., max_length=500)
    job_description: str | None = None

    location: str | None = Field(None, max_length=255)
    remote_policy: str | None = Field(None, max_length=50)

    salary_min: int | None = None
    salary_max: int | None = None
    salary_currency: str = Field(default="USD", max_length=10)

    required_skills: list[str] | None = None
    preferred_skills: list[str] | None = None
    required_keywords: list[str] | None = None

    posted_date: datetime | None = None
    expires_date: datetime | None = None

    status: str = Field(default="new", max_length=50)
    match_score: float | None = None
    match_reasons: dict | None = None

    interest_level: int | None = Field(None, ge=1, le=5, description="User interest rating 1-5")
    interest_notes: str | None = None

    raw_data: dict | None = None


class JobPostingCreate(JobPostingBase):
    """Schema for creating a job posting."""
    pass


class JobPostingUpdate(BaseModel):
    """Schema for updating a job posting."""

    company_id: UUID | None = None
    application_url: str | None = None
    status: str | None = None
    match_score: float | None = None
    match_reasons: dict | None = None
    interest_level: int | None = Field(None, ge=1, le=5)
    interest_notes: str | None = None

    model_config = ConfigDict(extra="forbid")


class JobPostingResponse(JobPostingBase):
    """Schema for job posting responses."""

    id: UUID
    discovered_date: datetime
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# Search Criteria Schemas
# ============================================================================

class SearchCriteriaBase(BaseModel):
    """Base schema for search criteria."""

    name: str = Field(..., max_length=255)
    description: str | None = None
    is_active: bool = True

    job_titles: list[str] | None = None

    locations: list[str] | None = None
    excluded_states: list[str] | None = None

    remote_policies: list[str] | None = None
    exclude_onsite: bool = False

    salary_minimum: int | None = None
    salary_target: int | None = None

    required_keywords: list[str] | None = None
    preferred_keywords: list[str] | None = None
    excluded_keywords: list[str] | None = None

    company_sizes: list[str] | None = None
    industries: list[str] | None = None
    excluded_industries: list[str] | None = None

    enabled_sources: list[str] | None = None

    auto_search_enabled: bool = False
    search_frequency_hours: int = 24

    scoring_weights: dict | None = Field(
        default={"salary": 0.3, "location": 0.2, "keywords": 0.3, "title": 0.2}
    )


class SearchCriteriaCreate(SearchCriteriaBase):
    """Schema for creating search criteria."""
    pass


class SearchCriteriaUpdate(BaseModel):
    """Schema for updating search criteria."""

    name: str | None = Field(None, max_length=255)
    description: str | None = None
    is_active: bool | None = None

    job_titles: list[str] | None = None
    locations: list[str] | None = None
    excluded_states: list[str] | None = None

    remote_policies: list[str] | None = None
    exclude_onsite: bool | None = None

    salary_minimum: int | None = None
    salary_target: int | None = None

    required_keywords: list[str] | None = None
    preferred_keywords: list[str] | None = None
    excluded_keywords: list[str] | None = None

    company_sizes: list[str] | None = None
    industries: list[str] | None = None
    excluded_industries: list[str] | None = None

    enabled_sources: list[str] | None = None

    auto_search_enabled: bool | None = None
    search_frequency_hours: int | None = None
    last_search_at: datetime | None = None
    next_search_at: datetime | None = None

    scoring_weights: dict | None = None

    model_config = ConfigDict(extra="forbid")


class SearchCriteriaResponse(SearchCriteriaBase):
    """Schema for search criteria responses."""

    id: UUID
    last_search_at: datetime | None = None
    next_search_at: datetime | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# Job Search History Schemas
# ============================================================================

class JobSearchHistoryBase(BaseModel):
    """Base schema for job search history."""

    search_criteria_id: UUID
    source: str = Field(..., max_length=100)
    query_params: dict | None = None

    jobs_found: int = 0
    jobs_matched: int = 0
    jobs_new: int = 0
    jobs_duplicate_exact: int = 0
    jobs_duplicate_fuzzy: int = 0
    dedup_stats: dict | None = None

    status: str = Field(default="running", max_length=50)
    error_message: str | None = None


class JobSearchHistoryCreate(JobSearchHistoryBase):
    """Schema for creating search history."""
    pass


class JobSearchHistoryResponse(JobSearchHistoryBase):
    """Schema for search history responses."""

    id: UUID
    started_at: datetime
    completed_at: datetime | None = None
    duration_seconds: int | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# Job Posting Match Schemas
# ============================================================================

class JobPostingMatchCreate(BaseModel):
    """Schema for creating job posting match."""

    job_posting_id: UUID
    search_criteria_id: UUID
    match_score: float | None = None
    match_reasons: dict | None = None


class JobPostingMatchResponse(BaseModel):
    """Schema for job posting match responses."""

    id: UUID
    job_posting_id: UUID
    search_criteria_id: UUID
    match_score: float | None = None
    match_reasons: dict | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# Query Schemas
# ============================================================================

class JobPostingQuery(BaseModel):
    """Schema for querying job postings."""

    status: str | None = None
    source: str | None = None
    min_score: float | None = None
    limit: int = Field(default=100, ge=1, le=500)
    offset: int = Field(default=0, ge=0)


class SearchCriteriaQuery(BaseModel):
    """Schema for querying search criteria."""

    is_active: bool | None = None
    limit: int = Field(default=100, ge=1, le=500)
    offset: int = Field(default=0, ge=0)
