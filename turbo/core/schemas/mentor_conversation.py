"""MentorConversation Pydantic schemas for validation and serialization."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class MentorConversationBase(BaseModel):
    """Base schema for MentorConversation."""

    role: str = Field(..., description="Message role: 'user' or 'assistant'")
    content: str = Field(..., description="Message content")
    context_snapshot: dict = Field(default={}, description="Snapshot of workspace context used for this message")

    @field_validator("role")
    @classmethod
    def validate_role(cls, v: str) -> str:
        """Validate role value."""
        if v not in ("user", "assistant"):
            raise ValueError("Role must be one of: user, assistant")
        return v


class MentorConversationCreate(MentorConversationBase):
    """Schema for creating a conversation message."""

    mentor_id: UUID = Field(..., description="Mentor ID")


class MentorConversationUpdate(BaseModel):
    """Schema for updating a conversation message."""

    content: str | None = None
    context_snapshot: dict | None = None


class MentorConversationResponse(MentorConversationBase):
    """Schema for conversation message response."""

    id: UUID
    mentor_id: UUID
    created_at: datetime

    model_config = {"from_attributes": True}


class ConversationHistoryResponse(BaseModel):
    """Schema for conversation history."""

    messages: list[MentorConversationResponse]
    total: int
    mentor_id: UUID


class SendMessageRequest(BaseModel):
    """Schema for sending a message to a mentor."""

    content: str = Field(..., min_length=1, description="User's message")


class SendMessageResponse(BaseModel):
    """Schema for message send response."""

    user_message: MentorConversationResponse
    assistant_message: MentorConversationResponse | None = None
    status: str = Field(..., description="Status: 'pending', 'completed', 'error'")
    error: str | None = Field(None, description="Error message if status is 'error'")
