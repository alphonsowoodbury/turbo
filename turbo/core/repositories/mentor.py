"""Mentor repository implementation."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from turbo.core.models.mentor import Mentor
from turbo.core.repositories.base import BaseRepository
from turbo.core.schemas.mentor import MentorCreate, MentorUpdate


class MentorRepository(BaseRepository[Mentor, MentorCreate, MentorUpdate]):
    """Repository for mentor data access."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, Mentor)

    async def get_by_workspace(
        self,
        workspace: str,
        work_company: str | None = None,
        is_active: bool | None = None,
        limit: int | None = None,
        offset: int | None = None,
    ) -> list[Mentor]:
        """Get mentors by workspace."""
        stmt = select(self._model).where(self._model.workspace == workspace)

        # For work workspace, filter by company if provided
        if workspace == "work" and work_company:
            stmt = stmt.where(self._model.work_company == work_company)

        # Filter by active status if specified
        if is_active is not None:
            stmt = stmt.where(self._model.is_active == is_active)

        # Order by created date (most recent first)
        stmt = stmt.order_by(self._model.created_at.desc())

        if offset:
            stmt = stmt.offset(offset)
        if limit:
            stmt = stmt.limit(limit)

        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_active_mentors(
        self,
        limit: int | None = None,
        offset: int | None = None,
    ) -> list[Mentor]:
        """Get all active mentors."""
        stmt = (
            select(self._model)
            .where(self._model.is_active == True)  # noqa: E712
            .order_by(self._model.created_at.desc())
        )

        if offset:
            stmt = stmt.offset(offset)
        if limit:
            stmt = stmt.limit(limit)

        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def deactivate_mentor(self, mentor_id: UUID) -> Mentor | None:
        """Deactivate a mentor."""
        mentor = await self.get_by_id(mentor_id)
        if mentor:
            mentor.is_active = False
            await self._session.flush()
            return mentor
        return None

    async def activate_mentor(self, mentor_id: UUID) -> Mentor | None:
        """Activate a mentor."""
        mentor = await self.get_by_id(mentor_id)
        if mentor:
            mentor.is_active = True
            await self._session.flush()
            return mentor
        return None
