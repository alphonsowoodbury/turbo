"""MentorConversation model for storing chat history."""

from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy import JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from turbo.core.models.base import Base


class MentorConversation(Base):
    """MentorConversation model representing a message in a mentor chat."""

    __tablename__ = "mentor_conversations"

    # Foreign keys
    mentor_id: Mapped[UUID] = mapped_column(
        ForeignKey("mentors.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Message fields
    role: Mapped[str] = mapped_column(
        String(20), nullable=False
    )  # 'user' or 'assistant'
    content: Mapped[str] = mapped_column(Text, nullable=False)

    # Context snapshot - what context was used for this message
    context_snapshot: Mapped[dict] = mapped_column(
        JSON, nullable=False, default={}
    )

    # Timestamp
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, nullable=False, index=True
    )

    # Relationships
    mentor = relationship("Mentor", back_populates="conversations")

    def __repr__(self) -> str:
        """String representation."""
        return f"<MentorConversation(id={self.id}, mentor_id={self.mentor_id}, role='{self.role}')>"
