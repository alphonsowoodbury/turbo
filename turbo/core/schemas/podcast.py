"""Pydantic schemas for Podcast models."""

from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, Field


# Podcast Show Schemas
class PodcastShowBase(BaseModel):
    """Base Podcast Show schema."""

    title: str = Field(..., max_length=500)
    description: Optional[str] = None
    author: Optional[str] = Field(None, max_length=255)
    publisher: Optional[str] = Field(None, max_length=255)
    feed_url: str = Field(..., max_length=2048)
    website_url: Optional[str] = Field(None, max_length=2048)
    image_url: Optional[str] = Field(None, max_length=2048)
    language: Optional[str] = Field(None, max_length=10)
    categories: Optional[str] = Field(None, max_length=500)
    explicit: bool = False
    is_subscribed: bool = True
    is_favorite: bool = False
    is_archived: bool = False
    auto_fetch: bool = False


class PodcastShowCreate(PodcastShowBase):
    """Schema for creating Podcast Show."""

    pass


class PodcastShowUpdate(BaseModel):
    """Schema for updating Podcast Show."""

    title: Optional[str] = Field(None, max_length=500)
    description: Optional[str] = None
    author: Optional[str] = Field(None, max_length=255)
    publisher: Optional[str] = Field(None, max_length=255)
    feed_url: Optional[str] = Field(None, max_length=2048)
    website_url: Optional[str] = Field(None, max_length=2048)
    image_url: Optional[str] = Field(None, max_length=2048)
    language: Optional[str] = Field(None, max_length=10)
    categories: Optional[str] = Field(None, max_length=500)
    explicit: Optional[bool] = None
    is_subscribed: Optional[bool] = None
    is_favorite: Optional[bool] = None
    is_archived: Optional[bool] = None
    auto_fetch: Optional[bool] = None


class PodcastShowResponse(PodcastShowBase):
    """Schema for Podcast Show response."""

    id: UUID
    last_fetched_at: Optional[datetime] = None
    total_episodes: int = 0
    listened_episodes: int = 0
    created_at: datetime
    updated_at: datetime

    class Config:
        """Pydantic config."""

        from_attributes = True


class PodcastShowWithEpisodes(PodcastShowResponse):
    """Schema for Podcast Show with episodes."""

    episodes: list["PodcastEpisodeResponse"] = []


# Podcast Episode Schemas
class PodcastEpisodeBase(BaseModel):
    """Base Podcast Episode schema."""

    show_id: UUID
    title: str = Field(..., max_length=500)
    description: Optional[str] = None
    summary: Optional[str] = None
    episode_number: Optional[int] = None
    season_number: Optional[int] = None
    audio_url: str = Field(..., max_length=2048)
    duration: Optional[int] = None
    file_size: Optional[int] = None
    mime_type: Optional[str] = Field(None, max_length=100)
    published_at: Optional[datetime] = None
    guid: Optional[str] = Field(None, max_length=500)
    transcript: Optional[str] = None
    transcript_url: Optional[str] = Field(None, max_length=2048)
    show_notes: Optional[str] = None
    image_url: Optional[str] = Field(None, max_length=2048)
    is_played: bool = False
    is_favorite: bool = False
    is_archived: bool = False
    is_downloaded: bool = False
    play_position: int = 0
    play_count: int = 0


class PodcastEpisodeCreate(PodcastEpisodeBase):
    """Schema for creating Podcast Episode."""

    pass


class PodcastEpisodeUpdate(BaseModel):
    """Schema for updating Podcast Episode."""

    title: Optional[str] = Field(None, max_length=500)
    description: Optional[str] = None
    summary: Optional[str] = None
    episode_number: Optional[int] = None
    season_number: Optional[int] = None
    audio_url: Optional[str] = Field(None, max_length=2048)
    duration: Optional[int] = None
    file_size: Optional[int] = None
    mime_type: Optional[str] = Field(None, max_length=100)
    published_at: Optional[datetime] = None
    guid: Optional[str] = Field(None, max_length=500)
    transcript: Optional[str] = None
    transcript_url: Optional[str] = Field(None, max_length=2048)
    show_notes: Optional[str] = None
    image_url: Optional[str] = Field(None, max_length=2048)
    is_played: Optional[bool] = None
    is_favorite: Optional[bool] = None
    is_archived: Optional[bool] = None
    is_downloaded: Optional[bool] = None
    play_position: Optional[int] = None
    play_count: Optional[int] = None


class PodcastEpisodeResponse(PodcastEpisodeBase):
    """Schema for Podcast Episode response."""

    id: UUID
    last_played_at: Optional[datetime] = None
    transcript_generated: bool = False
    transcript_generated_at: Optional[datetime] = None
    transcript_data: Optional[dict[str, Any]] = None  # Structured transcript with timestamps and speakers
    embedding_generated: bool = False
    created_at: datetime
    updated_at: datetime

    class Config:
        """Pydantic config."""

        from_attributes = True


class PodcastEpisodeWithShow(PodcastEpisodeResponse):
    """Schema for Podcast Episode with show details."""

    show: PodcastShowResponse


# Feed Schemas
class PodcastFeedURL(BaseModel):
    """Schema for podcast RSS feed URL."""

    url: str = Field(..., max_length=2048)


class PodcastFeedFetch(BaseModel):
    """Schema for fetching episodes from feed."""

    show_id: UUID
    limit: Optional[int] = Field(None, ge=1, le=100)


# Filter Schemas
class PodcastShowFilter(BaseModel):
    """Schema for filtering podcast shows."""

    is_subscribed: Optional[bool] = None
    is_favorite: Optional[bool] = None
    is_archived: Optional[bool] = None
    publisher: Optional[str] = None
    limit: int = Field(100, ge=1, le=1000)
    offset: int = Field(0, ge=0)


class PodcastEpisodeFilter(BaseModel):
    """Schema for filtering podcast episodes."""

    show_id: Optional[UUID] = None
    is_played: Optional[bool] = None
    is_favorite: Optional[bool] = None
    is_archived: Optional[bool] = None
    season_number: Optional[int] = None
    has_transcript: Optional[bool] = None
    limit: int = Field(100, ge=1, le=1000)
    offset: int = Field(0, ge=0)


# Progress Schemas
class PlayProgress(BaseModel):
    """Schema for updating play progress."""

    play_position: int = Field(..., ge=0)
    completed: bool = False


class TranscriptGenerate(BaseModel):
    """Schema for transcript generation request."""

    episode_id: UUID
    model: Optional[str] = Field(None, max_length=100)  # e.g., "whisper-1"