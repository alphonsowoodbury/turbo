"""Review request model for Staff requesting User feedback."""

from datetime import datetime
from typing import Optional
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from turbo.core.models.base import Base


class ReviewRequest(Base):
    """
    Review request from Staff to User.

    Used for scope validation, architecture review, product feedback, etc.
    """

    __tablename__ = "review_requests"

    # Foreign key to Staff (who is requesting)
    staff_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("staff.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Entity being reviewed (polymorphic)
    entity_type: Mapped[str] = mapped_column(
        String(50), nullable=False, index=True
    )  # issue | initiative | milestone | project
    entity_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False, index=True)

    # Request details
    request_type: Mapped[str] = mapped_column(
        String(50), nullable=False, index=True
    )  # scope_validation | feedback | approval | architecture_review | security_review
    description: Mapped[str] = mapped_column(Text, nullable=False)

    # Status
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="pending", index=True
    )  # pending | reviewed | dismissed

    # Timestamps
    # created_at inherited from BaseModel
    reviewed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Relationships
    staff = relationship("Staff", back_populates="review_requests")

    def __repr__(self) -> str:
        """String representation."""
        return f"<ReviewRequest(id={self.id}, staff_id={self.staff_id}, type={self.request_type}, status={self.status})>"
