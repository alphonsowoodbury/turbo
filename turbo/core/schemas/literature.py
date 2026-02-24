"""Pydantic schemas for Literature model."""

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


LiteratureType = Literal["article", "podcast", "book", "research_paper"]


class LiteratureBase(BaseModel):
    """Base Literature schema."""

    type: LiteratureType
    title: str = Field(..., max_length=500)
    url: str | None = Field(None, max_length=2048)
    content: str
    summary: str | None = None
    author: str | None = Field(None, max_length=255)
    source: str | None = Field(None, max_length=255)
    feed_url: str | None = Field(None, max_length=2048)
    published_at: datetime | None = None
    tags: str | None = Field(None, max_length=500)
    isbn: str | None = Field(None, max_length=20)
    doi: str | None = Field(None, max_length=255)
    duration: int | None = None
    audio_url: str | None = Field(None, max_length=2048)
    is_read: bool = False
    is_favorite: bool = False
    is_archived: bool = False
    progress: int | None = None


class LiteratureCreate(LiteratureBase):
    """Schema for creating Literature."""

    pass


class LiteratureUpdate(BaseModel):
    """Schema for updating Literature."""

    type: LiteratureType | None = None
    title: str | None = Field(None, max_length=500)
    url: str | None = Field(None, max_length=2048)
    content: str | None = None
    summary: str | None = None
    author: str | None = Field(None, max_length=255)
    source: str | None = Field(None, max_length=255)
    feed_url: str | None = Field(None, max_length=2048)
    published_at: datetime | None = None
    tags: str | None = Field(None, max_length=500)
    isbn: str | None = Field(None, max_length=20)
    doi: str | None = Field(None, max_length=255)
    duration: int | None = None
    audio_url: str | None = Field(None, max_length=2048)
    is_read: bool | None = None
    is_favorite: bool | None = None
    is_archived: bool | None = None
    progress: int | None = None


class LiteratureResponse(LiteratureBase):
    """Schema for Literature response."""

    id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class FeedURL(BaseModel):
    """Schema for RSS feed URL."""

    url: str = Field(..., max_length=2048)


class LiteratureFilter(BaseModel):
    """Schema for filtering literature."""

    type: LiteratureType | None = None
    source: str | None = None
    is_read: bool | None = None
    is_favorite: bool | None = None
    is_archived: bool | None = None
    limit: int = Field(100, ge=1, le=1000)
    offset: int = Field(0, ge=0)
