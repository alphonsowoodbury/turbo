"""Tag repository implementation."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from turbo.core.models.tag import Tag
from turbo.core.repositories.base import BaseRepository
from turbo.core.schemas.tag import TagCreate


class TagRepository(BaseRepository[Tag, TagCreate, TagCreate]):
    """Repository for tag data access."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, Tag)

    async def get_by_name(self, name: str) -> Tag | None:
        """Get tag by name."""
        stmt = select(self._model).where(self._model.name == name)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def search_by_name(self, name_pattern: str) -> list[Tag]:
        """Search tags by name pattern."""
        stmt = select(self._model).where(self._model.name.ilike(f"%{name_pattern}%"))
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_by_color(self, color: str) -> list[Tag]:
        """Get tags by color."""
        stmt = select(self._model).where(self._model.color == color)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_with_projects(self, id: UUID) -> Tag | None:
        """Get tag with its projects loaded."""
        stmt = (
            select(self._model)
            .options(selectinload(self._model.projects))
            .where(self._model.id == id)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_with_issues(self, id: UUID) -> Tag | None:
        """Get tag with its issues loaded."""
        stmt = (
            select(self._model)
            .options(selectinload(self._model.issues))
            .where(self._model.id == id)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_popular_tags(self, limit: int = 10) -> list[Tag]:
        """Get most popular tags (by usage count)."""
        # This would need a more complex query to count relationships
        # For now, return all tags sorted by name
        stmt = select(self._model).order_by(self._model.name).limit(limit)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_unused_tags(self) -> list[Tag]:
        """Get tags that are not used by any projects or issues."""
        # This would need a complex query with left joins
        # For now, return all tags (this would be implemented with proper joins)
        stmt = select(self._model)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def update(self, id: UUID, obj_in: TagCreate) -> Tag | None:
        """Update a tag record."""
        # Override to use TagCreate for updates (since TagUpdate is same as TagCreate)
        db_obj = await self.get_by_id(id)
        if not db_obj:
            return None

        update_data = obj_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            if hasattr(db_obj, field):
                setattr(db_obj, field, value)

        await self._session.commit()
        await self._session.refresh(db_obj)
        return db_obj
