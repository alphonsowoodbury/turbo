"""Initiative model definition."""

from typing import Optional

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, Mapped, mapped_column

from turbo.core.database.base import Base
from turbo.core.models.associations import initiative_documents, initiative_issues, initiative_tags


class Initiative(Base):
    """Initiative model representing a feature or technology-based grouping."""

    __tablename__ = "initiatives"

    # Required fields
    name = Column(String(100), nullable=False, index=True)
    initiative_key = Column(String(20), nullable=True, unique=True, index=True)  # e.g., "CNTXT-I1" (nullable for cross-project initiatives)
    initiative_number = Column(Integer, nullable=True)  # Sequential per project: 1, 2, 3... (nullable for cross-project initiatives)
    description = Column(String, nullable=False)
    status = Column(String(20), nullable=False, default="planning", index=True)

    # Date fields (optional for initiatives)
    start_date = Column(DateTime(timezone=True), nullable=True)
    target_date = Column(DateTime(timezone=True), nullable=True)

    # Polymorphic assignment
    assigned_to_type: Mapped[Optional[str]] = mapped_column(
        String(20), nullable=True, index=True
    )  # "user" | "staff"
    assigned_to_id: Mapped[Optional[UUID]] = mapped_column(
        UUID(as_uuid=True), nullable=True, index=True
    )

    # Foreign keys (optional - initiatives can be cross-project)
    project_id = Column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=True,  # Optional for initiatives
        index=True,
    )

    # Relationships
    project = relationship("Project", back_populates="initiatives")

    issues = relationship(
        "Issue", secondary=initiative_issues, back_populates="initiatives", lazy="select"
    )

    tags = relationship(
        "Tag", secondary=initiative_tags, back_populates="initiatives", lazy="select"
    )

    documents = relationship(
        "Document",
        secondary=initiative_documents,
        back_populates="initiatives",
        lazy="select",
    )

    def __repr__(self) -> str:
        """String representation of the initiative."""
        return f"<Initiative(id={self.id}, name='{self.name}', status='{self.status}')>"
