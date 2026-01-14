"""
Action Approval Model

Stores AI-requested actions that need human approval before execution.
Supports auto-execution for safe actions and approval queue for risky ones.
"""

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import Column, String, Text, DateTime, Boolean, JSON, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
import enum

from turbo.core.database.connection import Base


class ActionStatus(str, enum.Enum):
    """Status of an action approval request."""
    PENDING = "pending"           # Waiting for approval
    APPROVED = "approved"         # Approved by user
    DENIED = "denied"             # Denied by user
    EXECUTED = "executed"         # Successfully executed
    FAILED = "failed"             # Execution failed
    AUTO_EXECUTED = "auto_executed"  # Auto-executed (safe action)


class ActionRiskLevel(str, enum.Enum):
    """Risk level of an action."""
    SAFE = "safe"           # Auto-execute (e.g., add comment, add tag)
    LOW = "low"             # Auto-execute with notification (e.g., update description)
    MEDIUM = "medium"       # Requires approval (e.g., change status, assign)
    HIGH = "high"           # Requires approval (e.g., delete, close issue)
    CRITICAL = "critical"   # Requires approval + confirmation (e.g., bulk delete)


class ActionApproval(Base):
    """
    Action Approval Model

    Stores AI-requested actions that may need human approval.
    Supports auto-execution for safe actions and approval workflow for risky ones.
    """
    __tablename__ = "action_approvals"

    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Action metadata
    action_type = Column(String(100), nullable=False, index=True)  # e.g., "update_issue", "close_issue"
    action_description = Column(Text, nullable=False)  # Human-readable description
    risk_level = Column(SQLEnum(ActionRiskLevel), nullable=False, default=ActionRiskLevel.MEDIUM, index=True)

    # Action parameters (JSON)
    action_params = Column(JSON, nullable=False)  # Parameters for the action

    # Context
    entity_type = Column(String(50), nullable=False, index=True)  # issue, project, etc.
    entity_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    entity_title = Column(String(500), nullable=True)  # For display

    # AI context
    ai_reasoning = Column(Text, nullable=True)  # Why AI suggested this action
    ai_comment_id = Column(UUID(as_uuid=True), nullable=True)  # Related AI comment

    # Status tracking
    status = Column(SQLEnum(ActionStatus), nullable=False, default=ActionStatus.PENDING, index=True)

    # Approval/denial
    approved_at = Column(DateTime, nullable=True)
    approved_by = Column(String(255), nullable=True)  # User who approved
    denied_at = Column(DateTime, nullable=True)
    denied_by = Column(String(255), nullable=True)  # User who denied
    denial_reason = Column(Text, nullable=True)

    # Execution
    executed_at = Column(DateTime, nullable=True)
    execution_result = Column(JSON, nullable=True)  # Result data
    execution_error = Column(Text, nullable=True)  # Error message if failed
    executed_by_subagent = Column(Boolean, default=False)  # True if subagent was used
    subagent_name = Column(String(100), nullable=True)  # Which subagent executed it

    # Auto-execution
    auto_execute = Column(Boolean, default=False)  # True if action can auto-execute
    auto_executed_at = Column(DateTime, nullable=True)

    # Timestamps
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    expires_at = Column(DateTime, nullable=True)  # Optional expiration for time-sensitive actions

    def __repr__(self):
        return f"<ActionApproval(id={self.id}, action_type={self.action_type}, status={self.status}, risk_level={self.risk_level})>"

    def to_dict(self):
        """Convert to dictionary for API responses."""
        return {
            "id": str(self.id),
            "action_type": self.action_type,
            "action_description": self.action_description,
            "risk_level": self.risk_level.value,
            "action_params": self.action_params,
            "entity_type": self.entity_type,
            "entity_id": str(self.entity_id),
            "entity_title": self.entity_title,
            "ai_reasoning": self.ai_reasoning,
            "ai_comment_id": str(self.ai_comment_id) if self.ai_comment_id else None,
            "status": self.status.value,
            "approved_at": self.approved_at.isoformat() if self.approved_at else None,
            "approved_by": self.approved_by,
            "denied_at": self.denied_at.isoformat() if self.denied_at else None,
            "denied_by": self.denied_by,
            "denial_reason": self.denial_reason,
            "executed_at": self.executed_at.isoformat() if self.executed_at else None,
            "execution_result": self.execution_result,
            "execution_error": self.execution_error,
            "executed_by_subagent": self.executed_by_subagent,
            "subagent_name": self.subagent_name,
            "auto_execute": self.auto_execute,
            "auto_executed_at": self.auto_executed_at.isoformat() if self.auto_executed_at else None,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
        }
