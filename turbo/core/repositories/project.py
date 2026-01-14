"""Project repository implementation."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from turbo.core.models.project import Project
from turbo.core.repositories.base import BaseRepository
from turbo.core.schemas.project import ProjectCreate, ProjectUpdate


class ProjectRepository(BaseRepository[Project, ProjectCreate, ProjectUpdate]):
    """Repository for project data access."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, Project)

    async def get_by_status(self, status: str) -> list[Project]:
        """Get projects by status."""
        stmt = select(self._model).where(self._model.status == status)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def search_by_name(self, name_pattern: str) -> list[Project]:
        """Search projects by name pattern."""
        stmt = select(self._model).where(self._model.name.ilike(f"%{name_pattern}%"))
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_with_issues(self, id: UUID) -> Project | None:
        """Get project with its issues loaded."""
        stmt = (
            select(self._model)
            .options(selectinload(self._model.issues))
            .where(self._model.id == id)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_with_documents(self, id: UUID) -> Project | None:
        """Get project with its documents loaded."""
        stmt = (
            select(self._model)
            .options(selectinload(self._model.documents))
            .where(self._model.id == id)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_with_tags(self, id: UUID) -> Project | None:
        """Get project with its tags loaded."""
        stmt = (
            select(self._model)
            .options(selectinload(self._model.tags))
            .where(self._model.id == id)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_archived(
        self, limit: int | None = None, offset: int | None = None
    ) -> list[Project]:
        """Get archived projects."""
        stmt = select(self._model).where(self._model.is_archived)
        if offset:
            stmt = stmt.offset(offset)
        if limit:
            stmt = stmt.limit(limit)

        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_active(
        self, limit: int | None = None, offset: int | None = None
    ) -> list[Project]:
        """Get active (non-archived) projects."""
        stmt = select(self._model).where(~self._model.is_archived)
        if offset:
            stmt = stmt.offset(offset)
        if limit:
            stmt = stmt.limit(limit)

        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_by_priority(self, priority: str) -> list[Project]:
        """Get projects by priority."""
        stmt = select(self._model).where(self._model.priority == priority)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_high_priority_projects(self) -> list[Project]:
        """Get high priority and critical projects."""
        stmt = select(self._model).where(self._model.priority.in_(["high", "critical"]))
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_by_workspace(
        self,
        workspace: str,
        work_company: str | None = None,
        limit: int | None = None,
        offset: int | None = None,
    ) -> list[Project]:
        """Get projects by workspace, optionally filtered by company for work workspace."""
        stmt = select(self._model).where(self._model.workspace == workspace)

        # For work workspace, optionally filter by company
        if workspace == "work" and work_company:
            stmt = stmt.where(self._model.work_company == work_company)

        if offset:
            stmt = stmt.offset(offset)
        if limit:
            stmt = stmt.limit(limit)

        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_all_filtered(
        self,
        workspace: str | None = None,
        work_company: str | None = None,
        status: str | None = None,
        limit: int | None = None,
        offset: int | None = None,
    ) -> list[Project]:
        """Get all projects with optional workspace and status filtering."""
        stmt = select(self._model)

        if workspace:
            stmt = stmt.where(self._model.workspace == workspace)
            if workspace == "work" and work_company:
                stmt = stmt.where(self._model.work_company == work_company)

        if status:
            stmt = stmt.where(self._model.status == status)

        if offset:
            stmt = stmt.offset(offset)
        if limit:
            stmt = stmt.limit(limit)

        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_by_key(self, project_key: str) -> Project | None:
        """Get project by its human-readable key (e.g., 'CNTXT', 'TURBO')."""
        stmt = select(self._model).where(self._model.project_key == project_key)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()
