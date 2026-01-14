"""Staff conversation model for chat history with AI staff members."""

from datetime import datetime
from typing import Optional
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, String, Text, Boolean
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from turbo.core.models.base import Base


class StaffConversation(Base):
    """
    Conversation messages with Staff members.

    Supports both 1-on-1 chats and group discussions.
    """

    __tablename__ = "staff_conversations"

    # Foreign key to Staff
    staff_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("staff.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Message content
    message_type: Mapped[str] = mapped_column(
        String(20), nullable=False
    )  # user | assistant
    content: Mapped[str] = mapped_column(Text, nullable=False)

    # Group discussion support (Phase 2+)
    is_group_discussion: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )
    group_discussion_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True), nullable=True, index=True
    )

    # Timestamp is inherited from BaseModel (created_at)

    # Relationships
    staff = relationship("Staff", back_populates="conversations")

    def __repr__(self) -> str:
        """String representation."""
        preview = self.content[:50] + "..." if len(self.content) > 50 else self.content
        return f"<StaffConversation(id={self.id}, staff_id={self.staff_id}, type={self.message_type}, preview='{preview}')>"
