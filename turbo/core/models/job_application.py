"""JobApplication model definition for career management."""

from datetime import datetime
from typing import Optional

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, Mapped, mapped_column

from turbo.core.database.base import Base
from turbo.core.models.associations import job_application_tags


class JobApplication(Base):
    """JobApplication model for tracking job applications and interview progress."""

    __tablename__ = "job_applications"

    # Foreign keys
    company_id: Mapped[Optional[UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=True,
        index=True
    )
    resume_id: Mapped[Optional[UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("resumes.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    project_id: Mapped[Optional[UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )  # Optional: portfolio project used
    cover_letter_id: Mapped[Optional[UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("documents.id", ondelete="SET NULL"),
        nullable=True
    )
    referrer_contact_id: Mapped[Optional[UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("network_contacts.id", ondelete="SET NULL"),
        nullable=True
    )

    # Job details
    job_title = Column(String(255), nullable=False, index=True)
    job_description = Column(Text, nullable=True)
    job_url = Column(String(500), nullable=True)
    salary_min = Column(Integer, nullable=True)
    salary_max = Column(Integer, nullable=True)
    location = Column(String(255), nullable=True)
    remote_policy = Column(String(50), nullable=True)

    # Application status
    status = Column(
        String(50),
        nullable=False,
        default="researching",
        index=True
    )  # researching, interested, applied, screening, phone_screen, technical_interview, onsite, offer, negotiating, accepted, rejected, withdrawn, ghosted
    application_date = Column(DateTime(timezone=True), nullable=True, index=True)
    last_contact_date = Column(DateTime(timezone=True), nullable=True)
    next_followup_date = Column(DateTime(timezone=True), nullable=True, index=True)

    # Application materials
    resume_version = Column(String(50), nullable=True)  # Track which version was sent

    # Tracking
    source = Column(String(100), nullable=True, index=True)  # e.g., "LinkedIn", "Indeed", "Referral", "Company Website"

    # Interview tracking
    interview_count = Column(Integer, default=0)
    interview_notes = Column(Text, nullable=True)

    # Response tracking
    response_time_hours = Column(Integer, nullable=True)  # Time from application to first response
    rejection_reason = Column(Text, nullable=True)

    # Metadata
    notes = Column(Text, nullable=True)

    # Relationships
    company = relationship("Company", back_populates="job_applications")
    resume = relationship("Resume", foreign_keys=[resume_id])
    project = relationship("Project", foreign_keys=[project_id])
    cover_letter = relationship("Document", foreign_keys=[cover_letter_id])
    referrer = relationship("NetworkContact", foreign_keys=[referrer_contact_id])

    tags = relationship(
        "Tag",
        secondary=job_application_tags,
        back_populates="job_applications",
        lazy="select"
    )

    def __repr__(self) -> str:
        """String representation of the job application."""
        return f"<JobApplication(id={self.id}, job_title='{self.job_title}', status='{self.status}')>"
