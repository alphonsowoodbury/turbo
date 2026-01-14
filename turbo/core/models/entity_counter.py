"""ProjectEntityCounter model for tracking sequential entity numbers."""

from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from turbo.core.database.base import CompositeBase


class ProjectEntityCounter(CompositeBase):
    """
    Tracks the next sequential number for each entity type within a project.

    This enables generating unique keys like:
    - CNTXT-1, CNTXT-2 (issues)
    - CNTXT-M1, CNTXT-M2 (milestones)
    - CNTXT-I1, CNTXT-I2 (initiatives)
    - CNTXT-D1, CNTXT-D2 (documents)
    """

    __tablename__ = "project_entity_counters"

    # Composite primary key: project_id + entity_type
    project_id = Column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        primary_key=True,
        nullable=False,
    )

    entity_type = Column(
        String(20),
        primary_key=True,
        nullable=False,
    )  # "issue", "milestone", "initiative", "document"

    # The next number to assign
    next_number = Column(Integer, nullable=False, default=1)

    # Note: No relationship to Project since we use CompositeBase (different declarative base)
    # The ForeignKey constraint is sufficient for data integrity

    def __repr__(self) -> str:
        """String representation of the counter."""
        return f"<ProjectEntityCounter(project_id={self.project_id}, type={self.entity_type}, next={self.next_number})>"
