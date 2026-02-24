"""Pydantic schemas for Podcast models."""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


# Podcast Show Schemas
class PodcastShowBase(BaseModel):
    """Base Podcast Show schema."""

    title: str = Field(..., max_length=500)
    description: str | None = None
    author: str | None = Field(None, max_length=255)
    publisher: str | None = Field(None, max_length=255)
    feed_url: str = Field(..., max_length=2048)
    website_url: str | None = Field(None, max_length=2048)
    image_url: str | None = Field(None, max_length=2048)
    language: str | None = Field(None, max_length=10)
    categories: str | None = Field(None, max_length=500)
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

    title: str | None = Field(None, max_length=500)
    description: str | None = None
    author: str | None = Field(None, max_length=255)
    publisher: str | None = Field(None, max_length=255)
    feed_url: str | None = Field(None, max_length=2048)
    website_url: str | None = Field(None, max_length=2048)
    image_url: str | None = Field(None, max_length=2048)
    language: str | None = Field(None, max_length=10)
    categories: str | None = Field(None, max_length=500)
    explicit: bool | None = None
    is_subscribed: bool | None = None
    is_favorite: bool | None = None
    is_archived: bool | None = None
    auto_fetch: bool | None = None


class PodcastShowResponse(PodcastShowBase):
    """Schema for Podcast Show response."""

    id: UUID
    last_fetched_at: datetime | None = None
    total_episodes: int = 0
    listened_episodes: int = 0
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PodcastShowWithEpisodes(PodcastShowResponse):
    """Schema for Podcast Show with episodes."""

    episodes: list["PodcastEpisodeResponse"] = []


# Podcast Episode Schemas
class PodcastEpisodeBase(BaseModel):
    """Base Podcast Episode schema."""

    show_id: UUID
    title: str = Field(..., max_length=500)
    description: str | None = None
    summary: str | None = None
    episode_number: int | None = None
    season_number: int | None = None
    audio_url: str = Field(..., max_length=2048)
    duration: int | None = None
    file_size: int | None = None
    mime_type: str | None = Field(None, max_length=100)
    published_at: datetime | None = None
    guid: str | None = Field(None, max_length=500)
    transcript: str | None = None
    transcript_url: str | None = Field(None, max_length=2048)
    show_notes: str | None = None
    image_url: str | None = Field(None, max_length=2048)
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

    title: str | None = Field(None, max_length=500)
    description: str | None = None
    summary: str | None = None
    episode_number: int | None = None
    season_number: int | None = None
    audio_url: str | None = Field(None, max_length=2048)
    duration: int | None = None
    file_size: int | None = None
    mime_type: str | None = Field(None, max_length=100)
    published_at: datetime | None = None
    guid: str | None = Field(None, max_length=500)
    transcript: str | None = None
    transcript_url: str | None = Field(None, max_length=2048)
    show_notes: str | None = None
    image_url: str | None = Field(None, max_length=2048)
    is_played: bool | None = None
    is_favorite: bool | None = None
    is_archived: bool | None = None
    is_downloaded: bool | None = None
    play_position: int | None = None
    play_count: int | None = None


class PodcastEpisodeResponse(PodcastEpisodeBase):
    """Schema for Podcast Episode response."""

    id: UUID
    last_played_at: datetime | None = None
    transcript_generated: bool = False
    transcript_generated_at: datetime | None = None
    transcript_data: dict[str, Any] | None = None  # Structured transcript with timestamps and speakers
    embedding_generated: bool = False
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


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
    limit: int | None = Field(None, ge=1, le=100)


# Filter Schemas
class PodcastShowFilter(BaseModel):
    """Schema for filtering podcast shows."""

    is_subscribed: bool | None = None
    is_favorite: bool | None = None
    is_archived: bool | None = None
    publisher: str | None = None
    limit: int = Field(100, ge=1, le=1000)
    offset: int = Field(0, ge=0)


class PodcastEpisodeFilter(BaseModel):
    """Schema for filtering podcast episodes."""

    show_id: UUID | None = None
    is_played: bool | None = None
    is_favorite: bool | None = None
    is_archived: bool | None = None
    season_number: int | None = None
    has_transcript: bool | None = None
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
    model: str | None = Field(None, max_length=100)  # e.g., "whisper-1"
