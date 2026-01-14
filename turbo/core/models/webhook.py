"""Webhook models for event-driven integrations."""

from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, String, Boolean, Integer, Text
from sqlalchemy import JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, Mapped, mapped_column
from typing import Optional

from turbo.core.database.base import Base


class Webhook(Base):
    """Webhook configuration for external integrations."""

    __tablename__ = "webhooks"

    # Required fields
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    url: Mapped[str] = mapped_column(String(1000), nullable=False)
    secret: Mapped[str] = mapped_column(String(500), nullable=False)  # For HMAC signature

    # Event configuration
    events: Mapped[list] = mapped_column(JSON, nullable=False, default=list)  # List of events to subscribe to

    # Optional fields
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, index=True)

    # Retry configuration
    max_retries: Mapped[int] = mapped_column(Integer, default=3, nullable=False)
    timeout_seconds: Mapped[int] = mapped_column(Integer, default=30, nullable=False)

    # Headers to send with webhook (e.g., authorization)
    headers: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True, default=dict)

    # Relationships
    deliveries = relationship(
        "WebhookDelivery",
        back_populates="webhook",
        cascade="all, delete-orphan",
        lazy="dynamic"
    )


class WebhookDelivery(Base):
    """Audit log for webhook delivery attempts."""

    __tablename__ = "webhook_deliveries"

    # Foreign keys
    webhook_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("webhooks.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Event details
    event_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    payload: Mapped[dict] = mapped_column(JSON, nullable=False)

    # Delivery details
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        index=True
    )  # "success", "failed", "pending", "retrying"

    response_status_code: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    response_body: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Retry tracking
    attempt_number: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    delivered_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    next_retry_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )

    # Relationships
    webhook = relationship("Webhook", back_populates="deliveries")
