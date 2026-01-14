"""Work Log model for tracking time spent on issues."""

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import relationship

from turbo.core.database.base import Base


class WorkLog(Base):
    """
    Track work sessions on issues.

    Records when work started, when it ended, who did the work,
    and the associated git commit.
    """

    __tablename__ = "issue_work_logs"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    issue_id = Column(PGUUID(as_uuid=True), ForeignKey("issues.id", ondelete="CASCADE"), nullable=False)

    # Timestamps
    started_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    ended_at = Column(DateTime, nullable=True)

    # Who performed the work
    started_by = Column(String(50), nullable=False)  # 'user', 'ai:context', 'ai:turbo'

    # Git worktree information
    worktree_path = Column(String(500), nullable=True)  # Path to git worktree (e.g., ~/worktrees/Project-CNTXT-1)
    branch_name = Column(String(100), nullable=True)  # Git branch name (e.g., CNTXT-1/fix-auth-bug)

    # Git commit reference
    commit_url = Column(String(500), nullable=True)

    # Standard timestamps
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    issue = relationship("Issue", back_populates="work_logs")

    @property
    def time_spent_seconds(self) -> int | None:
        """Calculate time spent in seconds. Returns None if work is still in progress."""
        if not self.ended_at:
            return None
        delta = self.ended_at - self.started_at
        return int(delta.total_seconds())

    @property
    def time_spent_minutes(self) -> int | None:
        """Calculate time spent in minutes. Returns None if work is still in progress."""
        seconds = self.time_spent_seconds
        return int(seconds / 60) if seconds is not None else None

    @property
    def is_active(self) -> bool:
        """Check if this work session is still active (not ended)."""
        return self.ended_at is None

    def __repr__(self) -> str:
        status = "active" if self.is_active else f"{self.time_spent_minutes}min"
        return f"<WorkLog(issue_id={self.issue_id}, started_by={self.started_by}, {status})>"
