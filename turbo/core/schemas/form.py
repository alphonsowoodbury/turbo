"""Pydantic schemas for forms."""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class FormCreate(BaseModel):
    """Schema for creating a form."""

    title: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    schema: dict[str, Any] = Field(..., description="Form schema with fields")

    # Optional entity attachments
    issue_id: UUID | None = None
    document_id: UUID | None = None
    project_id: UUID | None = None

    # Creator info
    created_by: str = "system"
    created_by_type: str = "ai"  # 'user' or 'ai'

    # Workflow configuration
    on_submit: dict[str, Any] | None = None

    model_config = {"from_attributes": True}


class FormUpdate(BaseModel):
    """Schema for updating a form."""

    title: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = None
    schema: dict[str, Any] | None = None
    status: str | None = None
    on_submit: dict[str, Any] | None = None

    model_config = {"from_attributes": True}


class FormResponse(BaseModel):
    """Schema for form response."""

    id: UUID
    title: str
    description: str | None
    schema: dict[str, Any]
    status: str

    issue_id: UUID | None
    document_id: UUID | None
    project_id: UUID | None

    created_by: str
    created_by_type: str

    on_submit: dict[str, Any] | None

    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class FormResponseCreate(BaseModel):
    """Schema for creating a form response (user submission)."""

    responses: dict[str, Any] = Field(..., description="Field responses")
    responded_by: str = "user"
    responded_by_type: str = "user"  # 'user' or 'ai'

    model_config = {"from_attributes": True}


class FormResponseUpdate(BaseModel):
    """Schema for updating a form response."""

    responses: dict[str, Any]
    is_complete: bool | None = None

    model_config = {"from_attributes": True}


class FormResponseResponse(BaseModel):
    """Schema for form response response (returned to API)."""

    id: UUID
    form_id: UUID
    responses: dict[str, Any]
    responded_by: str
    responded_by_type: str
    is_complete: bool
    completed_at: datetime | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class FormResponseAuditResponse(BaseModel):
    """Schema for form response audit log entry."""

    id: UUID
    response_id: UUID
    field_id: str
    old_value: dict[str, Any] | None
    new_value: dict[str, Any] | None
    changed_by: str
    changed_by_type: str
    changed_at: datetime

    model_config = {"from_attributes": True}
