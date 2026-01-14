"""Mentor model for AI assistants powered by Claude Code."""

from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, String, Text
from sqlalchemy import JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from turbo.core.models.base import Base


class Mentor(Base):
    """Mentor model representing an AI assistant with workspace-specific context."""

    __tablename__ = "mentors"

    # Core fields
    name: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    persona: Mapped[str] = mapped_column(Text, nullable=False)

    # Workspace context
    workspace: Mapped[str] = mapped_column(
        String(20), nullable=False, default="personal", index=True
    )
    work_company: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # Configuration
    context_preferences: Mapped[dict] = mapped_column(
        JSON,
        nullable=False,
        default={
            "include_projects": True,
            "include_issues": True,
            "include_documents": True,
            "include_influencers": True,
            "max_items": 10,
        },
    )
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, index=True)

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
    conversations = relationship(
        "MentorConversation",
        back_populates="mentor",
        cascade="all, delete-orphan",
        lazy="select",
        order_by="MentorConversation.created_at",
    )

    def __repr__(self) -> str:
        """String representation."""
        return f"<Mentor(id={self.id}, name='{self.name}', workspace='{self.workspace}')>"
