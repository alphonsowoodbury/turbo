"""Group discussion model for All Hands and staff group chats."""

from datetime import datetime
from typing import Optional, TYPE_CHECKING
from uuid import UUID

from sqlalchemy import DateTime, String, Text, Boolean, Integer
from sqlalchemy import JSON
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from turbo.core.models.base import Base

if TYPE_CHECKING:
    from turbo.core.models.staff_conversation import StaffConversation


class GroupDiscussion(Base):
    """
    Group discussion room for staff members.

    Supports multi-staff conversations like "All Hands" meetings where
    multiple AI staff members can discuss topics together.
    """

    __tablename__ = "group_discussions"

    # Discussion metadata
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Discussion type: all_hands, department, ad_hoc
    discussion_type: Mapped[str] = mapped_column(
        String(50), nullable=False, default="all_hands"
    )

    # Participants (list of staff IDs)
    participant_ids: Mapped[list] = mapped_column(
        JSON, nullable=False, default=list
    )

    # Status: active, archived
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="active"
    )

    # Message count for quick stats
    message_count: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0
    )

    # Last activity timestamp
    last_activity_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Settings
    settings: Mapped[dict] = mapped_column(
        JSON,
        nullable=False,
        default=lambda: {
            "auto_summarize": True,
            "allow_user_participation": True,
            "max_messages": None,
        },
    )

    def __repr__(self) -> str:
        """String representation."""
        return f"<GroupDiscussion(id={self.id}, name='{self.name}', type={self.discussion_type}, participants={len(self.participant_ids)}, messages={self.message_count})>"
