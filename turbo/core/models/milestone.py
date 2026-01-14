"""Milestone model definition."""

from typing import Optional

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, Mapped, mapped_column

from turbo.core.database.base import Base
from turbo.core.models.associations import milestone_documents, milestone_issues, milestone_tags


class Milestone(Base):
    """Milestone model representing a project milestone."""

    __tablename__ = "milestones"

    # Required fields
    name = Column(String(100), nullable=False, index=True)
    milestone_key = Column(String(20), nullable=False, unique=True, index=True)  # e.g., "CNTXT-M1"
    milestone_number = Column(Integer, nullable=False)  # Sequential per project: 1, 2, 3...
    description = Column(String, nullable=False)
    status = Column(String(20), nullable=False, default="planned", index=True)

    # Date fields
    start_date = Column(DateTime(timezone=True), nullable=True)
    due_date = Column(DateTime(timezone=True), nullable=False)

    # Polymorphic assignment
    assigned_to_type: Mapped[Optional[str]] = mapped_column(
        String(20), nullable=True, index=True
    )  # "user" | "staff"
    assigned_to_id: Mapped[Optional[UUID]] = mapped_column(
        UUID(as_uuid=True), nullable=True, index=True
    )

    # Foreign keys
    project_id = Column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Relationships
    project = relationship("Project", back_populates="milestones")

    issues = relationship(
        "Issue", secondary=milestone_issues, back_populates="milestones", lazy="select"
    )

    tags = relationship(
        "Tag", secondary=milestone_tags, back_populates="milestones", lazy="select"
    )

    documents = relationship(
        "Document",
        secondary=milestone_documents,
        back_populates="milestones",
        lazy="select",
    )

    def __repr__(self) -> str:
        """String representation of the milestone."""
        return f"<Milestone(id={self.id}, name='{self.name}', project_id={self.project_id})>"