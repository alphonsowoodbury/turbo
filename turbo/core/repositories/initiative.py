"""Initiative repository implementation."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from turbo.core.models.initiative import Initiative
from turbo.core.models.project import Project
from turbo.core.repositories.base import BaseRepository
from turbo.core.schemas.initiative import InitiativeCreate, InitiativeUpdate


class InitiativeRepository(BaseRepository[Initiative, InitiativeCreate, InitiativeUpdate]):
    """Repository for initiative data access."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, Initiative)

    async def get_by_project(self, project_id: UUID) -> list[Initiative]:
        """Get initiatives by project ID."""
        stmt = (
            select(self._model)
            .options(
                selectinload(self._model.issues),
                selectinload(self._model.tags),
                selectinload(self._model.documents),
            )
            .where(self._model.project_id == project_id)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_by_status(self, status: str) -> list[Initiative]:
        """Get initiatives by status."""
        stmt = (
            select(self._model)
            .options(
                selectinload(self._model.issues),
                selectinload(self._model.tags),
                selectinload(self._model.documents),
            )
            .where(self._model.status == status)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_with_issues(self, id: UUID) -> Initiative | None:
        """Get initiative with its issues loaded."""
        stmt = (
            select(self._model)
            .options(selectinload(self._model.issues))
            .where(self._model.id == id)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_with_tags(self, id: UUID) -> Initiative | None:
        """Get initiative with its tags loaded."""
        stmt = (
            select(self._model)
            .options(selectinload(self._model.tags))
            .where(self._model.id == id)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_with_documents(self, id: UUID) -> Initiative | None:
        """Get initiative with its documents loaded."""
        stmt = (
            select(self._model)
            .options(selectinload(self._model.documents))
            .where(self._model.id == id)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_with_all_relations(self, id: UUID) -> Initiative | None:
        """Get initiative with all relations loaded."""
        stmt = (
            select(self._model)
            .options(
                selectinload(self._model.issues),
                selectinload(self._model.tags),
                selectinload(self._model.documents),
                selectinload(self._model.project),
            )
            .where(self._model.id == id)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_all_with_relations(
        self, limit: int | None = None, offset: int | None = None
    ) -> list[Initiative]:
        """Get all initiatives with relations loaded for accurate counts."""
        stmt = select(self._model).options(
            selectinload(self._model.issues),
            selectinload(self._model.tags),
            selectinload(self._model.documents),
        )
        if limit is not None:
            stmt = stmt.limit(limit)
        if offset is not None:
            stmt = stmt.offset(offset)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_by_workspace(
        self,
        workspace: str,
        work_company: str | None = None,
        limit: int | None = None,
        offset: int | None = None,
    ) -> list[Initiative]:
        """Get initiatives by workspace (filtering by project's workspace).

        Note: Initiatives may have project_id=None. Those are excluded from workspace filtering.
        """
        stmt = (
            select(self._model)
            .join(Project, self._model.project_id == Project.id)
            .where(Project.workspace == workspace)
            .options(
                selectinload(self._model.issues),
                selectinload(self._model.tags),
                selectinload(self._model.documents),
            )
        )

        # For work workspace, optionally filter by company
        if workspace == "work" and work_company:
            stmt = stmt.where(Project.work_company == work_company)

        if offset:
            stmt = stmt.offset(offset)
        if limit:
            stmt = stmt.limit(limit)

        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_by_key(self, initiative_key: str) -> Initiative | None:
        """Get initiative by its human-readable key (e.g., 'CNTXT-I1')."""
        stmt = select(self._model).where(self._model.initiative_key == initiative_key)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

