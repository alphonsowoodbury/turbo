"""Terminal session model for tracking active terminal sessions."""

from datetime import datetime
from typing import TYPE_CHECKING, Optional
from uuid import UUID, uuid4

from sqlalchemy import JSON, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from turbo.core.models.base import Base

if TYPE_CHECKING:
    from turbo.core.models.issue import Issue
    from turbo.core.models.project import Project


class TerminalSession(Base):
    """Terminal session model for tracking active shells."""

    __tablename__ = "terminal_sessions"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    user_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    session_id: Mapped[str] = mapped_column(
        String(255), unique=True, nullable=False, index=True
    )

    # Context
    project_id: Mapped[Optional[UUID]] = mapped_column(
        ForeignKey("projects.id", ondelete="SET NULL"), nullable=True, index=True
    )
    issue_id: Mapped[Optional[UUID]] = mapped_column(
        ForeignKey("issues.id", ondelete="SET NULL"), nullable=True, index=True
    )

    # Terminal configuration
    shell: Mapped[str] = mapped_column(String(100), default="/bin/bash")
    working_directory: Mapped[str] = mapped_column(Text, nullable=False)
    environment_vars: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    # Session state
    pid: Mapped[Optional[int]] = mapped_column(nullable=True)
    is_active: Mapped[bool] = mapped_column(default=True, index=True)
    last_activity: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, nullable=False
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, nullable=False
    )
    ended_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Relationships
    project: Mapped[Optional["Project"]] = relationship(
        "Project", back_populates="terminal_sessions", foreign_keys=[project_id]
    )
    issue: Mapped[Optional["Issue"]] = relationship(
        "Issue", back_populates="terminal_sessions", foreign_keys=[issue_id]
    )

    def __repr__(self) -> str:
        """Return string representation."""
        return f"<TerminalSession(id={self.id}, session_id={self.session_id}, active={self.is_active})>"
