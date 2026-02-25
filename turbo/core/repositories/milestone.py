"""Milestone repository implementation."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from turbo.core.models.milestone import Milestone
from turbo.core.models.project import Project
from turbo.core.repositories.base import BaseRepository
from turbo.core.schemas.milestone import MilestoneCreate, MilestoneUpdate


class MilestoneRepository(BaseRepository[Milestone, MilestoneCreate, MilestoneUpdate]):
    """Repository for milestone data access."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, Milestone)

    async def get_by_project(
        self, project_id: UUID, sort_by: str | None = None, sort_order: str = "desc"
    ) -> list[Milestone]:
        """Get milestones by project ID."""
        stmt = select(self._model).where(self._model.project_id == project_id)
        stmt = self._apply_sorting(stmt, sort_by, sort_order)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_by_status(
        self, status: str, sort_by: str | None = None, sort_order: str = "desc"
    ) -> list[Milestone]:
        """Get milestones by status."""
        stmt = select(self._model).where(self._model.status == status)
        stmt = self._apply_sorting(stmt, sort_by, sort_order)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_with_issues(self, id: UUID) -> Milestone | None:
        """Get milestone with its issues loaded."""
        stmt = (
            select(self._model)
            .options(selectinload(self._model.issues))
            .where(self._model.id == id)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_with_tags(self, id: UUID) -> Milestone | None:
        """Get milestone with its tags loaded."""
        stmt = (
            select(self._model)
            .options(selectinload(self._model.tags))
            .where(self._model.id == id)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_with_documents(self, id: UUID) -> Milestone | None:
        """Get milestone with its documents loaded."""
        stmt = (
            select(self._model)
            .options(selectinload(self._model.documents))
            .where(self._model.id == id)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_with_all_relations(self, id: UUID) -> Milestone | None:
        """Get milestone with all relations loaded."""
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

    async def get_by_workspace(
        self,
        workspace: str,
        work_company: str | None = None,
        limit: int | None = None,
        offset: int | None = None,
        sort_by: str | None = None,
        sort_order: str = "desc",
    ) -> list[Milestone]:
        """Get milestones by workspace (filtering by project's workspace)."""
        stmt = (
            select(self._model)
            .join(Project, self._model.project_id == Project.id)
            .where(Project.workspace == workspace)
        )

        # For work workspace, optionally filter by company
        if workspace == "work" and work_company:
            stmt = stmt.where(Project.work_company == work_company)

        stmt = self._apply_sorting(stmt, sort_by, sort_order)

        if offset:
            stmt = stmt.offset(offset)
        if limit:
            stmt = stmt.limit(limit)

        result = await self._session.execute(stmt)
        return list(result.scalars().all())
    async def get_by_key(self, milestone_key: str) -> Milestone | None:
        """Get milestone by its human-readable key (e.g., 'CNTXT-M1')."""
        stmt = select(self._model).where(self._model.milestone_key == milestone_key)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

