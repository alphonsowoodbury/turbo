"""Note model definition."""

from sqlalchemy import Column, String, Boolean, Text
from sqlalchemy.orm import relationship

from turbo.core.database.base import Base
from turbo.core.models.associations import note_tags


class Note(Base):
    """Note model representing quick thoughts and capture."""

    __tablename__ = "notes"

    # Required fields
    title = Column(String(500), nullable=False, index=True)

    # Optional fields
    content = Column(Text, nullable=True)

    # Workspace context
    workspace = Column(String(50), nullable=False, index=True, default="personal")
    work_company = Column(String(100), nullable=True, index=True)

    # Status
    is_archived = Column(Boolean, default=False, index=True)

    # Relationships
    tags = relationship(
        "Tag", secondary=note_tags, back_populates="notes", lazy="select"
    )

    def __repr__(self) -> str:
        """String representation of the note."""
        return f"<Note(id={self.id}, title='{self.title[:50]}')>"
