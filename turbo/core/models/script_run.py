"""Script Run model for tracking Python script executions."""

from datetime import datetime
from enum import Enum
from uuid import uuid4

from sqlalchemy import DateTime, Enum as SQLEnum, Float, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from turbo.core.models.base import Base


class ScriptRunStatus(str, Enum):
    """Script execution status."""

    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ScriptRun(Base):
    """Script Run model for tracking Python script executions."""

    __tablename__ = "script_runs"

    # Primary key
    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid4())
    )

    # Script identification
    script_name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    script_path: Mapped[str] = mapped_column(String(500), nullable=False)

    # Execution details
    command: Mapped[str | None] = mapped_column(Text, nullable=True)
    arguments: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Status and output
    status: Mapped[ScriptRunStatus] = mapped_column(
        SQLEnum(ScriptRunStatus), default=ScriptRunStatus.RUNNING, nullable=False, index=True
    )
    exit_code: Mapped[int | None] = mapped_column(Integer, nullable=True)
    output: Mapped[str | None] = mapped_column(Text, nullable=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Metrics
    duration_seconds: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    files_processed: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    records_affected: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Metadata
    triggered_by: Mapped[str | None] = mapped_column(String(100), nullable=True)  # manual, cron, webhook, etc.

    # Timestamps
    started_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False, index=True
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, index=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    def __repr__(self) -> str:
        return f"<ScriptRun {self.script_name} - {self.status}>"

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "script_name": self.script_name,
            "script_path": self.script_path,
            "command": self.command,
            "arguments": self.arguments,
            "status": self.status.value,
            "exit_code": self.exit_code,
            "output": self.output,
            "error": self.error,
            "duration_seconds": self.duration_seconds,
            "files_processed": self.files_processed,
            "records_affected": self.records_affected,
            "triggered_by": self.triggered_by,
            "started_at": self.started_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "updated_at": self.updated_at.isoformat(),
        }
