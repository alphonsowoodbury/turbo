"""Job posting models for job search functionality."""

from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy import  TIMESTAMP, Boolean, Float, Integer, String, Text, text, ForeignKey
from sqlalchemy import JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from turbo.core.database.base import Base


class JobPosting(Base):
    """Model for job postings discovered through automated searches."""

    __tablename__ = "job_postings"

    # Primary Key
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)

    # Source Information
    source: Mapped[str] = mapped_column(String(100), nullable=False)
    source_url: Mapped[str] = mapped_column(Text, nullable=False)
    application_url: Mapped[Optional[str]] = mapped_column(Text)
    external_id: Mapped[Optional[str]] = mapped_column(String(255))

    # Company Information
    company_id: Mapped[Optional[UUID]] = mapped_column()
    company_name: Mapped[str] = mapped_column(String(255), nullable=False)

    # Job Details
    job_title: Mapped[str] = mapped_column(String(500), nullable=False)
    job_description: Mapped[Optional[str]] = mapped_column(Text)

    # Location & Remote
    location: Mapped[Optional[str]] = mapped_column(String(255))
    remote_policy: Mapped[Optional[str]] = mapped_column(String(50))

    # Compensation
    salary_min: Mapped[Optional[int]] = mapped_column(Integer)
    salary_max: Mapped[Optional[int]] = mapped_column(Integer)
    salary_currency: Mapped[str] = mapped_column(String(10), default="USD")

    # Requirements & Skills
    required_skills: Mapped[Optional[list[str]]] = mapped_column(JSON)
    preferred_skills: Mapped[Optional[list[str]]] = mapped_column(JSON)
    required_keywords: Mapped[Optional[list[str]]] = mapped_column(JSON)

    # Metadata
    posted_date: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP)
    discovered_date: Mapped[datetime] = mapped_column(
        TIMESTAMP, server_default=text("CURRENT_TIMESTAMP")
    )
    expires_date: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP)

    # Status & Scoring
    status: Mapped[str] = mapped_column(String(50), default="new")
    match_score: Mapped[Optional[float]] = mapped_column(Float)
    match_reasons: Mapped[Optional[dict]] = mapped_column(JSON)

    # User Interest
    interest_level: Mapped[Optional[int]] = mapped_column(Integer)
    interest_notes: Mapped[Optional[str]] = mapped_column(Text)

    # Raw Data
    raw_data: Mapped[Optional[dict]] = mapped_column(JSON)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP, server_default=text("CURRENT_TIMESTAMP")
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP, server_default=text("CURRENT_TIMESTAMP")
    )

    # Relationships
    matches: Mapped[list["JobPostingMatch"]] = relationship(
        "JobPostingMatch", back_populates="job_posting", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<JobPosting(id={self.id}, title='{self.job_title}', company='{self.company_name}')>"


class SearchCriteria(Base):
    """Model for job search criteria and preferences."""

    __tablename__ = "search_criteria"

    # Primary Key
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)

    # Criteria Name
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Job Titles
    job_titles: Mapped[Optional[list[str]]] = mapped_column(JSON)

    # Location Preferences
    locations: Mapped[Optional[list[str]]] = mapped_column(JSON)
    excluded_states: Mapped[Optional[list[str]]] = mapped_column(JSON)

    # Remote Policy
    remote_policies: Mapped[Optional[list[str]]] = mapped_column(JSON)
    exclude_onsite: Mapped[bool] = mapped_column(Boolean, default=False)

    # Salary Requirements
    salary_minimum: Mapped[Optional[int]] = mapped_column(Integer)
    salary_target: Mapped[Optional[int]] = mapped_column(Integer)

    # Keywords
    required_keywords: Mapped[Optional[list[str]]] = mapped_column(JSON)
    preferred_keywords: Mapped[Optional[list[str]]] = mapped_column(JSON)
    excluded_keywords: Mapped[Optional[list[str]]] = mapped_column(JSON)

    # Company Filters
    company_sizes: Mapped[Optional[list[str]]] = mapped_column(JSON)
    industries: Mapped[Optional[list[str]]] = mapped_column(JSON)
    excluded_industries: Mapped[Optional[list[str]]] = mapped_column(JSON)

    # Job Boards
    enabled_sources: Mapped[Optional[list[str]]] = mapped_column(JSON)

    # Automation Settings
    auto_search_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    search_frequency_hours: Mapped[int] = mapped_column(Integer, default=24)
    last_search_at: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP)
    next_search_at: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP)

    # Scoring Weights
    scoring_weights: Mapped[Optional[dict]] = mapped_column(
        JSON,
        nullable=True,
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP, server_default=text("CURRENT_TIMESTAMP")
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP, server_default=text("CURRENT_TIMESTAMP")
    )

    # Relationships
    search_history: Mapped[list["JobSearchHistory"]] = relationship(
        "JobSearchHistory", back_populates="criteria", cascade="all, delete-orphan"
    )
    matches: Mapped[list["JobPostingMatch"]] = relationship(
        "JobPostingMatch", back_populates="criteria", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<SearchCriteria(id={self.id}, name='{self.name}', active={self.is_active})>"


class JobSearchHistory(Base):
    """Model for tracking job search executions."""

    __tablename__ = "job_search_history"

    # Primary Key
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)

    # Foreign Keys
    search_criteria_id: Mapped[UUID] = mapped_column(ForeignKey("search_criteria.id", ondelete="CASCADE"))

    # Search Details
    source: Mapped[str] = mapped_column(String(100), nullable=False)
    query_params: Mapped[Optional[dict]] = mapped_column(JSON)

    # Results
    jobs_found: Mapped[int] = mapped_column(Integer, default=0)
    jobs_matched: Mapped[int] = mapped_column(Integer, default=0)
    jobs_new: Mapped[int] = mapped_column(Integer, default=0)
    jobs_duplicate_exact: Mapped[int] = mapped_column(Integer, default=0)
    jobs_duplicate_fuzzy: Mapped[int] = mapped_column(Integer, default=0)
    dedup_stats: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    # Status
    status: Mapped[str] = mapped_column(String(50), default="running")
    error_message: Mapped[Optional[str]] = mapped_column(Text)

    # Timing
    started_at: Mapped[datetime] = mapped_column(
        TIMESTAMP, server_default=text("CURRENT_TIMESTAMP")
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP)
    duration_seconds: Mapped[Optional[int]] = mapped_column(Integer)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP, server_default=text("CURRENT_TIMESTAMP")
    )

    # Relationships
    criteria: Mapped["SearchCriteria"] = relationship(
        "SearchCriteria", back_populates="search_history"
    )

    def __repr__(self) -> str:
        return f"<JobSearchHistory(id={self.id}, source='{self.source}', status='{self.status}')>"


class JobPostingMatch(Base):
    """Model for linking job postings to search criteria (many-to-many)."""

    __tablename__ = "job_posting_matches"

    # Primary Key
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)

    # Foreign Keys
    job_posting_id: Mapped[UUID] = mapped_column(ForeignKey("job_postings.id", ondelete="CASCADE"))
    search_criteria_id: Mapped[UUID] = mapped_column(ForeignKey("search_criteria.id", ondelete="CASCADE"))

    # Match Details
    match_score: Mapped[Optional[float]] = mapped_column(Float)
    match_reasons: Mapped[Optional[dict]] = mapped_column(JSON)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP, server_default=text("CURRENT_TIMESTAMP")
    )

    # Relationships
    job_posting: Mapped["JobPosting"] = relationship(
        "JobPosting", back_populates="matches"
    )
    criteria: Mapped["SearchCriteria"] = relationship(
        "SearchCriteria", back_populates="matches"
    )

    def __repr__(self) -> str:
        return f"<JobPostingMatch(posting_id={self.job_posting_id}, criteria_id={self.search_criteria_id}, score={self.match_score})>"
