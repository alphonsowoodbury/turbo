"""Skill repository implementation."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from turbo.core.models.skill import Skill
from turbo.core.repositories.base import BaseRepository
from turbo.core.schemas.skill import SkillCreate, SkillUpdate


class SkillRepository(BaseRepository[Skill, SkillCreate, SkillUpdate]):
    """Repository for skill data access."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, Skill)

    async def get_by_name(self, name: str) -> Skill | None:
        """Get skill by name."""
        stmt = select(self._model).where(self._model.name == name)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def search_by_name(self, name_pattern: str) -> list[Skill]:
        """Search skills by name pattern."""
        stmt = select(self._model).where(self._model.name.ilike(f"%{name_pattern}%"))
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_by_category(
        self, category: str, limit: int | None = None, offset: int | None = None
    ) -> list[Skill]:
        """Get skills by category."""
        stmt = select(self._model).where(self._model.category == category)
        if offset:
            stmt = stmt.offset(offset)
        if limit:
            stmt = stmt.limit(limit)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_by_proficiency(
        self,
        proficiency_level: str,
        limit: int | None = None,
        offset: int | None = None,
    ) -> list[Skill]:
        """Get skills by proficiency level."""
        stmt = select(self._model).where(
            self._model.proficiency_level == proficiency_level
        )
        if offset:
            stmt = stmt.offset(offset)
        if limit:
            stmt = stmt.limit(limit)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_endorsed(
        self, limit: int | None = None, offset: int | None = None
    ) -> list[Skill]:
        """Get endorsed skills."""
        stmt = select(self._model).where(self._model.is_endorsed == True)
        if offset:
            stmt = stmt.offset(offset)
        if limit:
            stmt = stmt.limit(limit)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_with_tags(self, id: UUID) -> Skill | None:
        """Get skill with its tags loaded."""
        stmt = (
            select(self._model)
            .options(selectinload(self._model.tags))
            .where(self._model.id == id)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_recent(self, limit: int = 10) -> list[Skill]:
        """Get recently used skills."""
        stmt = (
            select(self._model)
            .where(self._model.last_used_at.is_not(None))
            .order_by(self._model.last_used_at.desc())
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())
