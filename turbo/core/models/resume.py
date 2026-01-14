"""Resume models for storing and managing resume data."""

from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy import JSON, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from turbo.core.database.base import Base


class Resume(Base):
    """Resume model representing uploaded and parsed resume data."""

    __tablename__ = "resumes"

    # Core fields
    title: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    file_path: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    file_type: Mapped[str] = mapped_column(String(20), nullable=False)  # pdf, markdown

    # Targeting
    is_primary: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    target_role: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    target_company: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)

    # Parsed data (raw JSON from AI extraction)
    parsed_data: Mapped[dict] = mapped_column(
        JSON,
        nullable=False,
        default={},
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    # Relationships
    sections = relationship(
        "ResumeSection",
        back_populates="resume",
        cascade="all, delete-orphan",
        lazy="select",
        order_by="ResumeSection.order",
    )

    def __repr__(self) -> str:
        """String representation."""
        return f"<Resume(id={self.id}, title='{self.title}', type='{self.file_type}')>"


class ResumeSection(Base):
    """Resume section model for reusable content blocks."""

    __tablename__ = "resume_sections"

    # Foreign keys
    resume_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("resumes.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Section details
    section_type: Mapped[str] = mapped_column(
        String(50), nullable=False, index=True
    )  # summary, experience, education, project, skill, other
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)

    # Ordering and visibility
    order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    # Section metadata (company, dates, location, etc.)
    section_metadata: Mapped[dict] = mapped_column(
        JSON,
        nullable=False,
        default={},
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    # Relationships
    resume = relationship("Resume", back_populates="sections")

    def __repr__(self) -> str:
        """String representation."""
        return f"<ResumeSection(id={self.id}, type='{self.section_type}', title='{self.title}')>"
