"""Company model definition for career management."""

from typing import Optional

from sqlalchemy import Boolean, Column, Float, Integer, JSON, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, Mapped, mapped_column

from turbo.core.database.base import Base
from turbo.core.models.associations import company_tags


class Company(Base):
    """Company model for job search tracking and research."""

    __tablename__ = "companies"

    # Basic info
    name = Column(String(255), nullable=False, index=True)
    website = Column(String(500), nullable=True)
    industry = Column(String(100), nullable=True, index=True)
    size = Column(String(50), nullable=True)  # e.g., "Startup (< 50)", "Medium (50-500)", "Large (500+)"
    location = Column(String(255), nullable=True)
    remote_policy = Column(String(50), nullable=True)  # e.g., "Remote", "Hybrid", "In-Office"

    # Status tracking
    target_status = Column(
        String(50),
        nullable=False,
        default="researching",
        index=True
    )  # researching, interested, applied, interviewing, offer, accepted, rejected, not_interested
    application_count = Column(Integer, default=0)

    # Research & notes
    research_notes = Column(Text, nullable=True)
    culture_notes = Column(Text, nullable=True)
    tech_stack = Column(JSON, nullable=True)  # Flexible storage for tech stack info
    glassdoor_rating = Column(Float, nullable=True)

    # Contact & social
    linkedin_url = Column(String(500), nullable=True)
    careers_page_url = Column(String(500), nullable=True)

    # Relationships
    job_applications = relationship(
        "JobApplication",
        back_populates="company",
        cascade="all, delete-orphan",
        lazy="select"
    )

    network_contacts = relationship(
        "NetworkContact",
        back_populates="company",
        lazy="select"
    )

    tags = relationship(
        "Tag",
        secondary=company_tags,
        back_populates="companies",
        lazy="select"
    )

    work_experiences = relationship(
        "WorkExperience",
        back_populates="company",
        lazy="select"
    )

    def __repr__(self) -> str:
        """String representation of the company."""
        return f"<Company(id={self.id}, name='{self.name}', status='{self.target_status}')>"
