"""Project model definition."""


from typing import Optional

from sqlalchemy import Boolean, Column, Float, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, Mapped, mapped_column

from turbo.core.database.base import Base
from turbo.core.models.associations import project_blueprints, project_tags


class Project(Base):
    """Project model representing a development project."""

    __tablename__ = "projects"

    # Required fields
    name = Column(String(100), nullable=False, index=True)
    project_key = Column(String(10), nullable=False, unique=True, index=True)  # e.g., "CNTXT", "TURBO"
    description = Column(String, nullable=False)
    status = Column(String(20), nullable=False, default="active", index=True)

    # Optional fields
    priority = Column(String(10), default="medium")
    completion_percentage = Column(Float, default=0.0)
    is_archived = Column(Boolean, default=False, index=True)

    # Git repository configuration
    repository_path = Column(String(500), nullable=True)  # Local filesystem path to git repo

    # Workspace fields for context filtering
    workspace = Column(String(20), nullable=False, default="personal", index=True)  # personal, freelance, work
    work_company = Column(String(100), nullable=True)  # For work workspace: company name (e.g., "JPMC")

    # Polymorphic assignment (who owns/is responsible for this project)
    assigned_to_type: Mapped[Optional[str]] = mapped_column(
        String(20), nullable=True, index=True
    )  # "user" | "staff"
    assigned_to_id: Mapped[Optional[UUID]] = mapped_column(
        UUID(as_uuid=True), nullable=True, index=True
    )

    # Relationships
    issues = relationship(
        "Issue", back_populates="project", cascade="all, delete-orphan", lazy="dynamic"
    )

    documents = relationship(
        "Document",
        back_populates="project",
        cascade="all, delete-orphan",
        lazy="select",
    )

    tags = relationship(
        "Tag", secondary=project_tags, back_populates="projects", lazy="select"
    )

    blueprints = relationship(
        "Blueprint", secondary=project_blueprints, back_populates="projects", lazy="select"
    )

    milestones = relationship(
        "Milestone",
        back_populates="project",
        cascade="all, delete-orphan",
        lazy="select",
    )

    initiatives = relationship(
        "Initiative",
        back_populates="project",
        cascade="all, delete-orphan",
        lazy="select",
    )

    terminal_sessions = relationship(
        "TerminalSession",
        back_populates="project",
        cascade="all, delete-orphan",
        lazy="select",
    )

    def __repr__(self) -> str:
        """String representation of the project."""
        return f"<Project(id={self.id}, name='{self.name}')>"
