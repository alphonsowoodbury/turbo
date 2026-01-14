"""Service for Literature business logic."""

from typing import Optional
from uuid import UUID

from turbo.core.models.literature import Literature
from turbo.core.repositories.literature import LiteratureRepository
from turbo.core.schemas.literature import LiteratureCreate, LiteratureUpdate
from turbo.core.utils import strip_emojis
from turbo.utils.content_extractor import extract_article_content, fetch_rss_feed


class LiteratureService:
    """Service for Literature operations."""

    def __init__(self, repository: LiteratureRepository):
        """Initialize service."""
        self.repository = repository

    async def create_literature(self, literature_data: LiteratureCreate) -> Literature:
        """Create new literature."""
        # Strip emojis from text fields
        if literature_data.title:
            literature_data.title = strip_emojis(literature_data.title)
        if literature_data.content:
            literature_data.content = strip_emojis(literature_data.content)

        return await self.repository.create(literature_data)

    async def get_literature(self, literature_id: UUID) -> Optional[Literature]:
        """Get literature by ID."""
        return await self.repository.get_by_id(literature_id)

    async def get_all_literature(
        self,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Literature]:
        """Get all literature."""
        return await self.repository.get_all(limit=limit, offset=offset)

    async def update_literature(
        self,
        literature_id: UUID,
        literature_data: LiteratureUpdate,
    ) -> Optional[Literature]:
        """Update literature."""
        # Strip emojis from text fields
        if literature_data.title:
            literature_data.title = strip_emojis(literature_data.title)
        if literature_data.content:
            literature_data.content = strip_emojis(literature_data.content)

        return await self.repository.update(literature_id, literature_data)

    async def delete_literature(self, literature_id: UUID) -> bool:
        """Delete literature."""
        return await self.repository.delete(literature_id)

    async def get_by_type(
        self,
        literature_type: str,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Literature]:
        """Get literature by type."""
        return await self.repository.get_by_type(literature_type, limit, offset)

    async def get_by_source(
        self,
        source: str,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Literature]:
        """Get literature by source."""
        return await self.repository.get_by_source(source, limit, offset)

    async def get_unread(
        self,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Literature]:
        """Get unread literature."""
        return await self.repository.get_unread(limit, offset)

    async def get_favorites(
        self,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Literature]:
        """Get favorite literature."""
        return await self.repository.get_favorites(limit, offset)

    async def mark_as_read(self, literature_id: UUID) -> Optional[Literature]:
        """Mark literature as read."""
        return await self.repository.mark_as_read(literature_id)

    async def toggle_favorite(self, literature_id: UUID) -> Optional[Literature]:
        """Toggle favorite status."""
        return await self.repository.toggle_favorite(literature_id)

    async def fetch_from_url(self, url: str) -> Literature:
        """Fetch and create article from URL."""
        # Extract content
        article_data = await extract_article_content(url)

        # Check if already exists
        existing = await self.repository.get_by_url(url)
        if existing:
            return existing

        # Create literature
        literature_create = LiteratureCreate(
            type="article",
            **article_data,
        )

        return await self.repository.create(literature_create)

    async def fetch_from_rss_feed(self, feed_url: str) -> list[Literature]:
        """Fetch articles from RSS feed."""
        articles_data = await fetch_rss_feed(feed_url)
        created_articles = []

        for article_data in articles_data:
            # Check if already exists
            url = article_data.get("url")
            if url:
                existing = await self.repository.get_by_url(url)
                if existing:
                    continue

            # Fetch full content if we only have summary
            if article_data.get("url") and not article_data.get("content"):
                try:
                    full_content = await extract_article_content(article_data["url"])
                    article_data["content"] = full_content.get("content", article_data.get("summary", ""))
                except Exception:
                    # Fall back to summary if content extraction fails
                    article_data["content"] = article_data.get("summary", "")

            # Create literature
            try:
                literature_create = LiteratureCreate(
                    type="article",
                    content=article_data.get("content") or article_data.get("summary", ""),
                    **article_data,
                )
                literature = await self.repository.create(literature_create)
                created_articles.append(literature)
            except Exception:
                # Skip articles that fail to create
                continue

        return created_articles