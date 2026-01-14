"""Blueprint database model."""

from datetime import datetime
from typing import Optional
from uuid import UUID as PyUUID, uuid4

from sqlalchemy import DateTime, String, Text, JSON, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from turbo.core.database.base import Base


class Blueprint(Base):
    """Blueprint model for architectural standards and patterns."""

    __tablename__ = "blueprints"
    __table_args__ = (
        UniqueConstraint('name', 'version', name='uq_blueprint_name_version'),
    )

    id: Mapped[PyUUID] = mapped_column(primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # 'architecture', 'testing', 'styling', 'database', 'api', 'deployment', 'custom'

    # JSON field to store the actual blueprint content
    # This can include patterns, standards, rules, templates, etc.
    content: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)

    # Optional fields
    version: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)

    # Polymorphic assignment (who owns/is responsible for this blueprint)
    assigned_to_type: Mapped[Optional[str]] = mapped_column(
        String(20), nullable=True, index=True
    )  # "user" | "staff"
    assigned_to_id: Mapped[Optional[PyUUID]] = mapped_column(
        UUID(as_uuid=True), nullable=True, index=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # Relationship with projects
    projects: Mapped[list["Project"]] = relationship(
        "Project", secondary="project_blueprints", back_populates="blueprints"
    )

    def __repr__(self) -> str:
        """String representation."""
        return f"<Blueprint(id={self.id}, name={self.name}, category={self.category})>"
