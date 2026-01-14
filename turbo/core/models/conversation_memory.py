"""Conversation memory models for long-term AI chat memory."""

from datetime import datetime
from typing import Optional
from uuid import UUID

from sqlalchemy import DateTime, Float, Index, String, Text, JSON, CheckConstraint
from sqlalchemy import JSON
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from turbo.core.models.base import Base


class ConversationMemory(Base):
    """
    Long-term memory extracted from conversations.

    Stores key facts, user preferences, decisions, and insights that persist
    beyond individual conversation sessions. Uses embeddings for semantic retrieval.
    """

    __tablename__ = "conversation_memories"

    __table_args__ = (
        Index('ix_memory_entity_type_id', 'entity_type', 'entity_id'),
        Index('ix_memory_type', 'memory_type'),
        Index('ix_memory_importance', 'importance'),
        CheckConstraint('importance >= 0 AND importance <= 1', name='ck_importance_range'),
        CheckConstraint('relevance_score >= 0 AND importance <= 1', name='ck_relevance_range'),
    )

    # Entity association (staff or mentor)
    entity_type: Mapped[str] = mapped_column(
        String(20), nullable=False, index=True
    )  # "staff" | "mentor"
    entity_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), nullable=False, index=True
    )

    # Memory metadata
    memory_type: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # "summary" | "fact" | "preference" | "decision" | "insight" | "entity_mention"

    # Memory content
    content: Mapped[str] = mapped_column(Text, nullable=False)

    # Importance scoring (higher = more important)
    importance: Mapped[float] = mapped_column(
        Float, nullable=False, default=0.5
    )  # 0.0 to 1.0

    # Relevance decay (decreases over time)
    relevance_score: Mapped[float] = mapped_column(
        Float, nullable=False, default=1.0
    )  # 0.0 to 1.0

    # Entities mentioned in this memory
    entities_mentioned: Mapped[Optional[dict]] = mapped_column(
        JSON, nullable=True
    )  # {"issues": ["uuid1", "uuid2"], "projects": ["uuid3"], "documents": [...]}

    # Semantic embedding for similarity search (384 dimensions for all-MiniLM-L6-v2)
    embedding: Mapped[Optional[list[float]]] = mapped_column(
        JSON, nullable=True
    )

    # Source message range
    source_message_ids: Mapped[Optional[list[str]]] = mapped_column(
        JSON, nullable=True
    )  # List of message UUIDs this memory was extracted from

    # Temporal metadata
    first_mentioned_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=datetime.utcnow
    )
    last_accessed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=datetime.utcnow
    )
    access_count: Mapped[int] = mapped_column(
        default=0, nullable=False
    )

    def __repr__(self) -> str:
        """String representation."""
        preview = self.content[:50] + "..." if len(self.content) > 50 else self.content
        return (
            f"<ConversationMemory(id={self.id}, type={self.memory_type}, "
            f"importance={self.importance:.2f}, preview='{preview}')>"
        )


class ConversationSummary(Base):
    """
    Summarized conversation segments for efficient context loading.

    Stores condensed versions of message ranges to reduce token usage
    when loading conversation history.
    """

    __tablename__ = "conversation_summaries"

    __table_args__ = (
        Index('ix_summary_entity_type_id', 'entity_type', 'entity_id'),
        Index('ix_summary_message_range', 'message_range_start', 'message_range_end'),
    )

    # Entity association (staff or mentor)
    entity_type: Mapped[str] = mapped_column(
        String(20), nullable=False
    )  # "staff" | "mentor"
    entity_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), nullable=False, index=True
    )

    # Summary content
    summary_text: Mapped[str] = mapped_column(Text, nullable=False)

    # Message range covered by this summary
    message_range_start: Mapped[int] = mapped_column(
        nullable=False
    )  # Message index (e.g., 1)
    message_range_end: Mapped[int] = mapped_column(
        nullable=False
    )  # Message index (e.g., 20)
    message_count: Mapped[int] = mapped_column(
        nullable=False
    )

    # Key topics discussed
    key_topics: Mapped[Optional[list[str]]] = mapped_column(
        JSON, nullable=True
    )  # ["authentication", "database schema", "deployment"]

    # Entities discussed in this segment
    entities_discussed: Mapped[Optional[dict]] = mapped_column(
        JSON, nullable=True
    )  # {"issues": [...], "projects": [...], "documents": [...]}

    # Decisions made
    decisions_made: Mapped[Optional[list[str]]] = mapped_column(
        JSON, nullable=True
    )  # ["Use PostgreSQL for main database", "Deploy to AWS"]

    # Semantic embedding for similarity search
    embedding: Mapped[Optional[list[float]]] = mapped_column(
        JSON, nullable=True
    )

    # Timestamps
    time_range_start: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    time_range_end: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"<ConversationSummary(id={self.id}, messages={self.message_range_start}-{self.message_range_end}, "
            f"topics={len(self.key_topics) if self.key_topics else 0})>"
        )
