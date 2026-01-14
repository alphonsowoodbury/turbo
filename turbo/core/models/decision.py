"""Decision model definition.

Decisions capture strategic and tactical choices with full rationale,
options considered, and constraints. They sit at the top of the hierarchy:
Decision → Initiative → Feature (Project) → Task (Issue)
"""

from typing import Optional
from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, String, Text
from sqlalchemy import JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, Mapped, mapped_column

from turbo.core.database.base import Base


class Decision(Base):
    """Decision model capturing strategic/tactical choices with context."""

    __tablename__ = "decisions"

    # Required fields
    title = Column(String(200), nullable=False, index=True)
    decision_key = Column(String(20), nullable=True, unique=True, index=True)  # e.g., "DEC-1"

    # The decision itself
    summary = Column(Text, nullable=False)  # Brief description of what was decided
    rationale = Column(Text, nullable=False)  # Why this decision was made

    # Context
    context = Column(Text, nullable=True)  # Background/situation that led to this decision
    constraints = Column(JSON, nullable=True)  # List of constraints that influenced the decision
    options_considered = Column(JSON, nullable=True)  # List of alternatives with pros/cons

    # Decision metadata
    decision_type = Column(
        String(30),
        nullable=False,
        default="tactical",
        index=True
    )  # "strategic" | "tactical" | "technical" | "product"

    status = Column(
        String(20),
        nullable=False,
        default="proposed",
        index=True
    )  # "proposed" | "approved" | "implemented" | "superseded" | "rejected"

    # Timing
    decided_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    superseded_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Links to superseding decision
    superseded_by_id: Mapped[Optional[UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("decisions.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Who made the decision
    decided_by = Column(String(255), nullable=True)  # User or "AI: model_name"

    # Impact tracking
    impact_areas = Column(JSON, nullable=True)  # List of affected areas/systems

    # Relationships
    superseded_by = relationship(
        "Decision",
        remote_side="Decision.id",
        foreign_keys=[superseded_by_id],
        backref="supersedes",
    )

    # Initiatives spawned from this decision
    initiatives = relationship(
        "Initiative",
        back_populates="decision",
        lazy="select",
    )

    def __repr__(self) -> str:
        """String representation of the decision."""
        return f"<Decision(id={self.id}, title='{self.title}', status='{self.status}')>"
