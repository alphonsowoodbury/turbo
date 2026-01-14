"""Literature model for storing articles, podcasts, books, and research papers."""

from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from turbo.core.models.base import Base
from turbo.core.models.associations import literature_tags


class Literature(Base):
    """Literature model for storing various content types."""

    __tablename__ = "literature"

    # Type of literature
    type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)  # article, podcast, book, research_paper

    # Content fields
    title: Mapped[str] = mapped_column(String(500), nullable=False, index=True)
    url: Mapped[Optional[str]] = mapped_column(String(2048), nullable=True, index=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Metadata
    author: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    source: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, index=True)
    feed_url: Mapped[Optional[str]] = mapped_column(String(2048), nullable=True)

    # Publication info
    published_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Book/Paper specific
    isbn: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    doi: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Podcast specific
    duration: Mapped[Optional[int]] = mapped_column(nullable=True)  # Duration in seconds
    audio_url: Mapped[Optional[str]] = mapped_column(String(2048), nullable=True)

    # Reading/Listening status
    is_read: Mapped[bool] = mapped_column(default=False, index=True)
    is_favorite: Mapped[bool] = mapped_column(default=False, index=True)
    is_archived: Mapped[bool] = mapped_column(default=False, index=True)

    # Progress tracking
    progress: Mapped[Optional[int]] = mapped_column(nullable=True)  # Progress percentage or position

    # Relationships
    tags = relationship(
        "Tag", secondary=literature_tags, back_populates="literature", lazy="select"
    )

    def __repr__(self) -> str:
        """String representation."""
        return f"<Literature {self.type}: {self.title[:50]}>"