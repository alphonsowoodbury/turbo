"""Webhook Pydantic schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, HttpUrl


class WebhookBase(BaseModel):
    """Base webhook schema with common fields."""

    name: str = Field(..., min_length=1, max_length=200)
    url: str = Field(..., min_length=1, max_length=1000)
    secret: str = Field(..., min_length=1, max_length=500)
    events: list[str] = Field(default_factory=list, description="List of events to subscribe to (e.g., 'issue.assigned', 'issue.updated')")
    description: str | None = Field(default=None)
    is_active: bool = Field(default=True)
    max_retries: int = Field(default=3, ge=0, le=10)
    timeout_seconds: int = Field(default=30, ge=1, le=300)
    headers: dict[str, str] | None = Field(default_factory=dict, description="Custom headers to send with webhook")

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate webhook name."""
        if not v.strip():
            raise ValueError("Name cannot be empty or whitespace")
        return v.strip()

    @field_validator("url")
    @classmethod
    def validate_url(cls, v: str) -> str:
        """Validate webhook URL."""
        if not v.strip():
            raise ValueError("URL cannot be empty or whitespace")
        # Basic URL validation
        if not v.startswith(("http://", "https://")):
            raise ValueError("URL must start with http:// or https://")
        return v.strip()

    @field_validator("secret")
    @classmethod
    def validate_secret(cls, v: str) -> str:
        """Validate webhook secret."""
        if not v.strip():
            raise ValueError("Secret cannot be empty or whitespace")
        if len(v.strip()) < 16:
            raise ValueError("Secret must be at least 16 characters long")
        return v.strip()

    @field_validator("events")
    @classmethod
    def validate_events(cls, v: list[str]) -> list[str]:
        """Validate webhook events."""
        if not v:
            raise ValueError("At least one event must be specified")
        valid_events = {
            "issue.assigned",
            "issue.updated",
            "issue.created",
            "issue.deleted",
            "project.created",
            "project.updated",
        }
        for event in v:
            if event not in valid_events:
                raise ValueError(f"Invalid event: {event}. Valid events: {', '.join(valid_events)}")
        return v


class WebhookCreate(WebhookBase):
    """Schema for creating new webhooks."""
    pass


class WebhookUpdate(BaseModel):
    """Schema for updating webhooks (all fields optional)."""

    name: str | None = Field(default=None, min_length=1, max_length=200)
    url: str | None = Field(default=None, min_length=1, max_length=1000)
    secret: str | None = Field(default=None, min_length=1, max_length=500)
    events: list[str] | None = Field(default=None)
    description: str | None = Field(default=None)
    is_active: bool | None = Field(default=None)
    max_retries: int | None = Field(default=None, ge=0, le=10)
    timeout_seconds: int | None = Field(default=None, ge=1, le=300)
    headers: dict[str, str] | None = Field(default=None)


class WebhookResponse(WebhookBase):
    """Schema for webhook API responses."""

    id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class WebhookDeliveryBase(BaseModel):
    """Base webhook delivery schema."""

    event_type: str = Field(..., min_length=1, max_length=100)
    payload: dict = Field(..., description="Event payload sent to webhook")
    status: str = Field(..., pattern="^(success|failed|pending|retrying)$")
    response_status_code: int | None = Field(default=None)
    response_body: str | None = Field(default=None)
    error_message: str | None = Field(default=None)
    attempt_number: int = Field(default=1, ge=1)
    delivered_at: datetime | None = Field(default=None)
    next_retry_at: datetime | None = Field(default=None)


class WebhookDeliveryCreate(BaseModel):
    """Schema for creating webhook deliveries."""

    webhook_id: UUID
    event_type: str = Field(..., min_length=1, max_length=100)
    payload: dict
    status: str = Field(default="pending", pattern="^(success|failed|pending|retrying)$")


class WebhookDeliveryResponse(WebhookDeliveryBase):
    """Schema for webhook delivery API responses."""

    id: UUID
    webhook_id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class WebhookTestRequest(BaseModel):
    """Schema for testing webhook endpoint."""

    event_type: str = Field(default="test.ping", description="Event type to test")
    payload: dict | None = Field(default_factory=lambda: {"test": True}, description="Test payload")
