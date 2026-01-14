"""Repository for Literature database operations."""

from typing import Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from turbo.core.models.literature import Literature
from turbo.core.repositories.base import BaseRepository
from turbo.core.schemas.literature import LiteratureCreate, LiteratureUpdate


class LiteratureRepository(BaseRepository[Literature, LiteratureCreate, LiteratureUpdate]):
    """Repository for Literature operations."""

    def __init__(self, session: AsyncSession):
        """Initialize repository."""
        super().__init__(session, Literature)

    async def get_by_url(self, url: str) -> Optional[Literature]:
        """Get literature by URL."""
        result = await self._session.execute(
            select(Literature).where(Literature.url == url)
        )
        return result.scalars().first()

    async def get_by_type(
        self,
        literature_type: str,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Literature]:
        """Get literature by type."""
        result = await self._session.execute(
            select(Literature)
            .where(Literature.type == literature_type)
            .order_by(Literature.published_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(result.scalars().all())

    async def get_by_source(
        self,
        source: str,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Literature]:
        """Get literature by source."""
        result = await self._session.execute(
            select(Literature)
            .where(Literature.source == source)
            .order_by(Literature.published_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(result.scalars().all())

    async def get_unread(
        self,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Literature]:
        """Get unread literature."""
        result = await self._session.execute(
            select(Literature)
            .where(Literature.is_read == False)  # noqa: E712
            .where(Literature.is_archived == False)  # noqa: E712
            .order_by(Literature.published_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(result.scalars().all())

    async def get_favorites(
        self,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Literature]:
        """Get favorite literature."""
        result = await self._session.execute(
            select(Literature)
            .where(Literature.is_favorite == True)  # noqa: E712
            .order_by(Literature.published_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(result.scalars().all())

    async def mark_as_read(self, literature_id: UUID) -> Optional[Literature]:
        """Mark literature as read."""
        literature = await self.get_by_id(literature_id)
        if literature:
            literature.is_read = True
            await self._session.commit()
            await self._session.refresh(literature)
        return literature

    async def toggle_favorite(self, literature_id: UUID) -> Optional[Literature]:
        """Toggle favorite status."""
        literature = await self.get_by_id(literature_id)
        if literature:
            literature.is_favorite = not literature.is_favorite
            await self._session.commit()
            await self._session.refresh(literature)
        return literature