"""Pydantic schemas for job posting and search criteria."""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict


# ============================================================================
# Job Posting Schemas
# ============================================================================

class JobPostingBase(BaseModel):
    """Base schema for job posting."""

    source: str = Field(..., max_length=100, description="Job board source")
    source_url: str = Field(..., description="Original job posting URL")
    application_url: Optional[str] = Field(None, description="Direct application URL (company's application page)")
    external_id: Optional[str] = Field(None, max_length=255, description="External platform job ID")

    company_id: Optional[UUID] = None
    company_name: str = Field(..., max_length=255)

    job_title: str = Field(..., max_length=500)
    job_description: Optional[str] = None

    location: Optional[str] = Field(None, max_length=255)
    remote_policy: Optional[str] = Field(None, max_length=50)

    salary_min: Optional[int] = None
    salary_max: Optional[int] = None
    salary_currency: str = Field(default="USD", max_length=10)

    required_skills: Optional[list[str]] = None
    preferred_skills: Optional[list[str]] = None
    required_keywords: Optional[list[str]] = None

    posted_date: Optional[datetime] = None
    expires_date: Optional[datetime] = None

    status: str = Field(default="new", max_length=50)
    match_score: Optional[float] = None
    match_reasons: Optional[dict] = None

    interest_level: Optional[int] = Field(None, ge=1, le=5, description="User interest rating 1-5")
    interest_notes: Optional[str] = None

    raw_data: Optional[dict] = None


class JobPostingCreate(JobPostingBase):
    """Schema for creating a job posting."""
    pass


class JobPostingUpdate(BaseModel):
    """Schema for updating a job posting."""

    company_id: Optional[UUID] = None
    application_url: Optional[str] = None
    status: Optional[str] = None
    match_score: Optional[float] = None
    match_reasons: Optional[dict] = None
    interest_level: Optional[int] = Field(None, ge=1, le=5)
    interest_notes: Optional[str] = None

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
    description: Optional[str] = None
    is_active: bool = True

    job_titles: Optional[list[str]] = None

    locations: Optional[list[str]] = None
    excluded_states: Optional[list[str]] = None

    remote_policies: Optional[list[str]] = None
    exclude_onsite: bool = False

    salary_minimum: Optional[int] = None
    salary_target: Optional[int] = None

    required_keywords: Optional[list[str]] = None
    preferred_keywords: Optional[list[str]] = None
    excluded_keywords: Optional[list[str]] = None

    company_sizes: Optional[list[str]] = None
    industries: Optional[list[str]] = None
    excluded_industries: Optional[list[str]] = None

    enabled_sources: Optional[list[str]] = None

    auto_search_enabled: bool = False
    search_frequency_hours: int = 24

    scoring_weights: Optional[dict] = Field(
        default={"salary": 0.3, "location": 0.2, "keywords": 0.3, "title": 0.2}
    )


class SearchCriteriaCreate(SearchCriteriaBase):
    """Schema for creating search criteria."""
    pass


class SearchCriteriaUpdate(BaseModel):
    """Schema for updating search criteria."""

    name: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    is_active: Optional[bool] = None

    job_titles: Optional[list[str]] = None
    locations: Optional[list[str]] = None
    excluded_states: Optional[list[str]] = None

    remote_policies: Optional[list[str]] = None
    exclude_onsite: Optional[bool] = None

    salary_minimum: Optional[int] = None
    salary_target: Optional[int] = None

    required_keywords: Optional[list[str]] = None
    preferred_keywords: Optional[list[str]] = None
    excluded_keywords: Optional[list[str]] = None

    company_sizes: Optional[list[str]] = None
    industries: Optional[list[str]] = None
    excluded_industries: Optional[list[str]] = None

    enabled_sources: Optional[list[str]] = None

    auto_search_enabled: Optional[bool] = None
    search_frequency_hours: Optional[int] = None
    last_search_at: Optional[datetime] = None
    next_search_at: Optional[datetime] = None

    scoring_weights: Optional[dict] = None

    model_config = ConfigDict(extra="forbid")


class SearchCriteriaResponse(SearchCriteriaBase):
    """Schema for search criteria responses."""

    id: UUID
    last_search_at: Optional[datetime] = None
    next_search_at: Optional[datetime] = None
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
    query_params: Optional[dict] = None

    jobs_found: int = 0
    jobs_matched: int = 0
    jobs_new: int = 0
    jobs_duplicate_exact: int = 0
    jobs_duplicate_fuzzy: int = 0
    dedup_stats: Optional[dict] = None

    status: str = Field(default="running", max_length=50)
    error_message: Optional[str] = None


class JobSearchHistoryCreate(JobSearchHistoryBase):
    """Schema for creating search history."""
    pass


class JobSearchHistoryResponse(JobSearchHistoryBase):
    """Schema for search history responses."""

    id: UUID
    started_at: datetime
    completed_at: Optional[datetime] = None
    duration_seconds: Optional[int] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# Job Posting Match Schemas
# ============================================================================

class JobPostingMatchCreate(BaseModel):
    """Schema for creating job posting match."""

    job_posting_id: UUID
    search_criteria_id: UUID
    match_score: Optional[float] = None
    match_reasons: Optional[dict] = None


class JobPostingMatchResponse(BaseModel):
    """Schema for job posting match responses."""

    id: UUID
    job_posting_id: UUID
    search_criteria_id: UUID
    match_score: Optional[float] = None
    match_reasons: Optional[dict] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# Query Schemas
# ============================================================================

class JobPostingQuery(BaseModel):
    """Schema for querying job postings."""

    status: Optional[str] = None
    source: Optional[str] = None
    min_score: Optional[float] = None
    limit: int = Field(default=100, ge=1, le=500)
    offset: int = Field(default=0, ge=0)


class SearchCriteriaQuery(BaseModel):
    """Schema for querying search criteria."""

    is_active: Optional[bool] = None
    limit: int = Field(default=100, ge=1, le=500)
    offset: int = Field(default=0, ge=0)
