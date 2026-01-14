"""SavedFilter model definition."""

from sqlalchemy import Column, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID

from turbo.core.database.base import Base


class SavedFilter(Base):
    """SavedFilter model for storing user's filter preferences."""

    __tablename__ = "saved_filters"

    # Filter metadata
    name = Column(String(100), nullable=False)
    description = Column(String(255), nullable=True)

    # Filter configuration (JSON string)
    filter_config = Column(Text, nullable=False)  # Stores JSON: {"status": "open", "priority": "high", etc}

    # Association with project
    project_id = Column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    def __repr__(self) -> str:
        """String representation of the saved filter."""
        return f"<SavedFilter(id={self.id}, name='{self.name}', project_id={self.project_id})>"