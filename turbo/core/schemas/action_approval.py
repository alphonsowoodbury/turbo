"""Action Approval Pydantic Schemas"""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from turbo.core.models.action_approval import ActionStatus, ActionRiskLevel


class ActionApprovalBase(BaseModel):
    """Base schema for action approvals."""
    action_type: str = Field(..., description="Type of action (e.g., 'update_issue', 'close_issue')")
    action_description: str = Field(..., description="Human-readable description of the action")
    risk_level: ActionRiskLevel = Field(default=ActionRiskLevel.MEDIUM, description="Risk level of the action")
    action_params: dict[str, Any] = Field(..., description="Parameters for the action")
    entity_type: str = Field(..., description="Type of entity (issue, project, etc.)")
    entity_id: UUID = Field(..., description="UUID of the entity")
    entity_title: str | None = Field(None, description="Title of the entity for display")
    ai_reasoning: str | None = Field(None, description="AI's reasoning for suggesting this action")
    ai_comment_id: UUID | None = Field(None, description="Related AI comment ID")


class ActionApprovalCreate(ActionApprovalBase):
    """Schema for creating a new action approval request."""
    auto_execute: bool = Field(default=False, description="Whether action can auto-execute")
    expires_at: datetime | None = Field(None, description="Optional expiration time")


class ActionApprovalUpdate(BaseModel):
    """Schema for updating an action approval."""
    status: ActionStatus | None = None
    approved_by: str | None = None
    denied_by: str | None = None
    denial_reason: str | None = None
    execution_result: dict[str, Any] | None = None
    execution_error: str | None = None
    executed_by_subagent: bool | None = None
    subagent_name: str | None = None


class ActionApprovalResponse(ActionApprovalBase):
    """Schema for action approval responses."""
    id: UUID
    status: ActionStatus
    auto_execute: bool

    # Approval/denial
    approved_at: datetime | None = None
    approved_by: str | None = None
    denied_at: datetime | None = None
    denied_by: str | None = None
    denial_reason: str | None = None

    # Execution
    executed_at: datetime | None = None
    execution_result: dict[str, Any] | None = None
    execution_error: str | None = None
    executed_by_subagent: bool
    subagent_name: str | None = None
    auto_executed_at: datetime | None = None

    # Timestamps
    created_at: datetime
    updated_at: datetime
    expires_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class ActionApprovalListResponse(BaseModel):
    """Schema for list of action approvals."""
    approvals: list[ActionApprovalResponse]
    total: int
    pending_count: int
    approved_count: int
    denied_count: int
    executed_count: int


class ApproveActionRequest(BaseModel):
    """Schema for approving an action."""
    approved_by: str = Field(..., description="User who is approving")
    execute_immediately: bool = Field(default=True, description="Execute immediately after approval")


class DenyActionRequest(BaseModel):
    """Schema for denying an action."""
    denied_by: str = Field(..., description="User who is denying")
    denial_reason: str | None = Field(None, description="Reason for denial")
