"""Pydantic schemas for Literature model."""

from datetime import datetime
from typing import Literal, Optional
from uuid import UUID

from pydantic import BaseModel, Field


LiteratureType = Literal["article", "podcast", "book", "research_paper"]


class LiteratureBase(BaseModel):
    """Base Literature schema."""

    type: LiteratureType
    title: str = Field(..., max_length=500)
    url: Optional[str] = Field(None, max_length=2048)
    content: str
    summary: Optional[str] = None
    author: Optional[str] = Field(None, max_length=255)
    source: Optional[str] = Field(None, max_length=255)
    feed_url: Optional[str] = Field(None, max_length=2048)
    published_at: Optional[datetime] = None
    tags: Optional[str] = Field(None, max_length=500)
    isbn: Optional[str] = Field(None, max_length=20)
    doi: Optional[str] = Field(None, max_length=255)
    duration: Optional[int] = None
    audio_url: Optional[str] = Field(None, max_length=2048)
    is_read: bool = False
    is_favorite: bool = False
    is_archived: bool = False
    progress: Optional[int] = None


class LiteratureCreate(LiteratureBase):
    """Schema for creating Literature."""

    pass


class LiteratureUpdate(BaseModel):
    """Schema for updating Literature."""

    type: Optional[LiteratureType] = None
    title: Optional[str] = Field(None, max_length=500)
    url: Optional[str] = Field(None, max_length=2048)
    content: Optional[str] = None
    summary: Optional[str] = None
    author: Optional[str] = Field(None, max_length=255)
    source: Optional[str] = Field(None, max_length=255)
    feed_url: Optional[str] = Field(None, max_length=2048)
    published_at: Optional[datetime] = None
    tags: Optional[str] = Field(None, max_length=500)
    isbn: Optional[str] = Field(None, max_length=20)
    doi: Optional[str] = Field(None, max_length=255)
    duration: Optional[int] = None
    audio_url: Optional[str] = Field(None, max_length=2048)
    is_read: Optional[bool] = None
    is_favorite: Optional[bool] = None
    is_archived: Optional[bool] = None
    progress: Optional[int] = None


class LiteratureResponse(LiteratureBase):
    """Schema for Literature response."""

    id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        """Pydantic config."""

        from_attributes = True


class FeedURL(BaseModel):
    """Schema for RSS feed URL."""

    url: str = Field(..., max_length=2048)


class LiteratureFilter(BaseModel):
    """Schema for filtering literature."""

    type: Optional[LiteratureType] = None
    source: Optional[str] = None
    is_read: Optional[bool] = None
    is_favorite: Optional[bool] = None
    is_archived: Optional[bool] = None
    limit: int = Field(100, ge=1, le=1000)
    offset: int = Field(0, ge=0)