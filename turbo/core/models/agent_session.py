"""Agent Session model for tracking AI agent activity."""

from datetime import datetime
from enum import Enum
from uuid import uuid4

from sqlalchemy import DateTime, Enum as SQLEnum, Float, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from turbo.core.models.base import Base


class AgentSessionStatus(str, Enum):
    """Agent session execution status."""

    IDLE = "idle"
    STARTING = "starting"
    PROCESSING = "processing"
    TYPING = "typing"
    COMPLETED = "completed"
    ERROR = "error"


class AgentSession(Base):
    """Agent Session model for tracking individual AI agent interactions."""

    __tablename__ = "agent_sessions"

    # Primary key
    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid4())
    )

    # Session tracking
    session_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)

    # Entity relationship
    entity_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    entity_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    entity_title: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Status
    status: Mapped[AgentSessionStatus] = mapped_column(
        SQLEnum(AgentSessionStatus), default=AgentSessionStatus.IDLE, nullable=False
    )

    # Error tracking
    error: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Metrics
    input_tokens: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    output_tokens: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    cost_usd: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    duration_seconds: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)

    # Context
    comment_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Timestamps
    started_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False, index=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, index=True)

    def __repr__(self) -> str:
        return f"<AgentSession {self.session_id} ({self.entity_type}/{self.entity_id}) - {self.status}>"

    def to_dict(self) -> dict:
        """Convert to dictionary matching the in-memory format."""
        return {
            "session_id": self.session_id,
            "entity_type": self.entity_type,
            "entity_id": self.entity_id,
            "entity_title": self.entity_title,
            "status": self.status.value,
            "error": self.error,
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "cost_usd": self.cost_usd,
            "duration_seconds": self.duration_seconds,
            "comment_count": self.comment_count,
            "started_at": self.started_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
        }
