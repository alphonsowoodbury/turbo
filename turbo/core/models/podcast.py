"""Podcast models for shows and episodes."""

from datetime import datetime
from typing import Optional
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, Boolean, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from turbo.core.models.base import Base


class PodcastShow(Base):
    """Podcast show/series model."""

    __tablename__ = "podcast_shows"

    # Basic info
    title: Mapped[str] = mapped_column(String(500), nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    author: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    publisher: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, index=True)

    # Feed info
    feed_url: Mapped[str] = mapped_column(String(2048), nullable=False, unique=True, index=True)
    website_url: Mapped[Optional[str]] = mapped_column(String(2048), nullable=True)
    image_url: Mapped[Optional[str]] = mapped_column(String(2048), nullable=True)

    # Metadata
    language: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    categories: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)  # Comma-separated
    explicit: Mapped[bool] = mapped_column(Boolean, default=False)

    # Subscription status
    is_subscribed: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    is_favorite: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    is_archived: Mapped[bool] = mapped_column(Boolean, default=False, index=True)

    # Auto-fetch settings
    auto_fetch: Mapped[bool] = mapped_column(Boolean, default=False)
    last_fetched_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Statistics
    total_episodes: Mapped[int] = mapped_column(Integer, default=0)
    listened_episodes: Mapped[int] = mapped_column(Integer, default=0)

    # Relationships
    episodes: Mapped[list["PodcastEpisode"]] = relationship(
        "PodcastEpisode",
        back_populates="show",
        cascade="all, delete-orphan",
        lazy="selectin"
    )

    def __repr__(self) -> str:
        """String representation."""
        return f"<PodcastShow: {self.title}>"


class PodcastEpisode(Base):
    """Podcast episode model."""

    __tablename__ = "podcast_episodes"

    # Show reference
    show_id: Mapped[UUID] = mapped_column(ForeignKey("podcast_shows.id", ondelete="CASCADE"), nullable=False, index=True)

    # Episode info
    title: Mapped[str] = mapped_column(String(500), nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Episode numbering
    episode_number: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, index=True)
    season_number: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, index=True)

    # Media info
    audio_url: Mapped[str] = mapped_column(String(2048), nullable=False)
    duration: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # Duration in seconds
    file_size: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # Size in bytes
    mime_type: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # Publication
    published_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    guid: Mapped[Optional[str]] = mapped_column(String(500), nullable=True, unique=True, index=True)  # RSS GUID

    # Content
    transcript: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # Full transcript text
    transcript_data: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)  # Structured transcript with timestamps and speakers
    transcript_url: Mapped[Optional[str]] = mapped_column(String(2048), nullable=True)
    show_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Image
    image_url: Mapped[Optional[str]] = mapped_column(String(2048), nullable=True)

    # Listening status
    is_played: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    is_favorite: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    is_archived: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    is_downloaded: Mapped[bool] = mapped_column(Boolean, default=False)

    # Progress tracking
    play_position: Mapped[int] = mapped_column(Integer, default=0)  # Position in seconds
    play_count: Mapped[int] = mapped_column(Integer, default=0)
    last_played_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # AI/ML processing
    transcript_generated: Mapped[bool] = mapped_column(Boolean, default=False)
    transcript_generated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    embedding_generated: Mapped[bool] = mapped_column(Boolean, default=False)  # For graph/semantic search

    # Relationships
    show: Mapped["PodcastShow"] = relationship("PodcastShow", back_populates="episodes")

    def __repr__(self) -> str:
        """String representation."""
        episode_info = f"S{self.season_number}E{self.episode_number}" if self.season_number and self.episode_number else f"#{self.episode_number}" if self.episode_number else ""
        return f"<PodcastEpisode {episode_info}: {self.title[:50]}>"