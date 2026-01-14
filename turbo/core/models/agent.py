"""Agent model for autonomous task execution."""

from datetime import datetime
from enum import Enum
from uuid import uuid4

from sqlalchemy import Boolean, DateTime, Enum as SQLEnum, String, Text, JSON
from sqlalchemy.orm import Mapped, mapped_column

from turbo.core.models.base import Base


class AgentType(str, Enum):
    """Types of agents."""

    PM_AGENT = "pm_agent"  # Project management agent
    RESEARCH_AGENT = "research_agent"  # Research and literature agent
    CODEBASE_AGENT = "codebase_agent"  # Codebase understanding agent
    WORKFLOW_AGENT = "workflow_agent"  # Automation agent


class AgentStatus(str, Enum):
    """Agent execution status."""

    IDLE = "idle"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    PAUSED = "paused"


class Agent(Base):
    """Agent model for autonomous task execution."""

    __tablename__ = "agents"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid4())
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    agent_type: Mapped[AgentType] = mapped_column(
        SQLEnum(AgentType), nullable=False
    )
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[AgentStatus] = mapped_column(
        SQLEnum(AgentStatus), default=AgentStatus.IDLE
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Configuration
    config: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)

    # Schedule
    schedule_cron: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # Execution tracking
    last_run_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    next_run_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    run_count: Mapped[int] = mapped_column(default=0)

    # Results
    last_result: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    def __repr__(self) -> str:
        return f"<Agent {self.name} ({self.agent_type})>"
