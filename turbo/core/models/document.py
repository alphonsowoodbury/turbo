"""Document model definition."""


from typing import Optional

from sqlalchemy import Column, ForeignKey, Integer, String, Text
from sqlalchemy import JSON, UUID
from sqlalchemy.orm import relationship, Mapped, mapped_column

from turbo.core.database.base import Base
from turbo.core.models.associations import initiative_documents, milestone_documents


class Document(Base):
    """Document model representing project documentation."""

    __tablename__ = "documents"

    # Required fields
    title = Column(String(200), nullable=False, index=True)
    document_key = Column(String(20), nullable=False, unique=True, index=True)  # e.g., "CNTXT-D1"
    document_number = Column(Integer, nullable=False)  # Sequential per project: 1, 2, 3...
    content = Column(Text, nullable=False)
    type = Column(String(50), nullable=False, default="specification")
    format = Column(String(20), nullable=False, default="markdown")
    status = Column(String(20), nullable=False, default="draft", index=True)  # draft, in_review, approved, published, archived

    # Optional fields
    version = Column(String(20), nullable=True)
    author = Column(String(255), nullable=True)  # Email address

    # Structured metadata (owner, update_frequency, review_cycle, etc.)
    doc_metadata = Column(JSON, nullable=True, default=dict)

    # Polymorphic assignment (who owns/is responsible for this document)
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
    project = relationship("Project", back_populates="documents")

    milestones = relationship(
        "Milestone", secondary=milestone_documents, back_populates="documents", lazy="select"
    )

    initiatives = relationship(
        "Initiative", secondary=initiative_documents, back_populates="documents", lazy="select"
    )

    def __repr__(self) -> str:
        """String representation of the document."""
        return f"<Document(id={self.id}, title='{self.title}')>"
