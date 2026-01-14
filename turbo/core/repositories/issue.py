"""Issue repository implementation."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from turbo.core.models.issue import Issue
from turbo.core.models.project import Project
from turbo.core.repositories.base import BaseRepository
from turbo.core.schemas.issue import IssueCreate, IssueUpdate


class IssueRepository(BaseRepository[Issue, IssueCreate, IssueUpdate]):
    """Repository for issue data access."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, Issue)

    async def get_by_project(self, project_id: UUID) -> list[Issue]:
        """Get issues by project ID."""
        stmt = select(self._model).where(self._model.project_id == project_id)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_by_status(self, status: str) -> list[Issue]:
        """Get issues by status."""
        stmt = select(self._model).where(self._model.status == status)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_by_type(self, issue_type: str) -> list[Issue]:
        """Get issues by type."""
        stmt = select(self._model).where(self._model.type == issue_type)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_by_assignee(self, assignee: str) -> list[Issue]:
        """Get issues by assignee."""
        stmt = select(self._model).where(self._model.assignee == assignee)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_by_priority(self, priority: str) -> list[Issue]:
        """Get issues by priority."""
        stmt = select(self._model).where(self._model.priority == priority)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def search_by_title(self, title_pattern: str) -> list[Issue]:
        """Search issues by title pattern."""
        stmt = select(self._model).where(self._model.title.ilike(f"%{title_pattern}%"))
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_open_issues(self) -> list[Issue]:
        """Get all open issues."""
        stmt = select(self._model).where(self._model.status == "open")
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_closed_issues(self) -> list[Issue]:
        """Get all closed issues."""
        stmt = select(self._model).where(self._model.status == "closed")
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_unassigned_issues(self) -> list[Issue]:
        """Get issues without assignee."""
        stmt = select(self._model).where(self._model.assignee.is_(None))
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_high_priority_issues(self) -> list[Issue]:
        """Get high priority and critical issues."""
        stmt = select(self._model).where(self._model.priority.in_(["high", "critical"]))
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_project_open_issues(self, project_id: UUID) -> list[Issue]:
        """Get open issues for a specific project."""
        stmt = select(self._model).where(
            (self._model.project_id == project_id) & (self._model.status == "open")
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_project_closed_issues(self, project_id: UUID) -> list[Issue]:
        """Get closed issues for a specific project."""
        stmt = select(self._model).where(
            (self._model.project_id == project_id) & (self._model.status == "closed")
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_with_project(self, id: UUID) -> Issue | None:
        """Get issue with its project loaded."""
        stmt = (
            select(self._model)
            .options(selectinload(self._model.project))
            .where(self._model.id == id)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_with_tags(self, id: UUID) -> Issue | None:
        """Get issue with its tags loaded."""
        stmt = (
            select(self._model)
            .options(selectinload(self._model.tags))
            .where(self._model.id == id)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_all_with_relationships(self) -> list[Issue]:
        """Get all issues with relationships eagerly loaded for refinement analysis."""
        stmt = select(self._model).options(
            selectinload(self._model.milestones),
            selectinload(self._model.tags),
            selectinload(self._model.initiatives),
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_by_project_with_relationships(self, project_id: UUID) -> list[Issue]:
        """Get issues by project with relationships eagerly loaded."""
        stmt = (
            select(self._model)
            .options(
                selectinload(self._model.milestones),
                selectinload(self._model.tags),
                selectinload(self._model.initiatives),
            )
            .where(self._model.project_id == project_id)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_by_workspace(
        self,
        workspace: str,
        work_company: str | None = None,
        limit: int | None = None,
        offset: int | None = None,
    ) -> list[Issue]:
        """Get issues by workspace (filtering by project's workspace)."""
        stmt = (
            select(self._model)
            .join(Project, self._model.project_id == Project.id)
            .where(Project.workspace == workspace)
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

    # Work Queue Methods

    async def get_work_queue(
        self,
        status: str | None = None,
        priority: str | None = None,
        limit: int | None = 100,
        offset: int | None = 0,
        include_unranked: bool = False,
    ) -> list[Issue]:
        """Get work queue sorted by work_rank."""
        stmt = select(self._model)

        # Filter by work_rank
        if not include_unranked:
            stmt = stmt.where(self._model.work_rank.isnot(None))

        # Optional filters
        if status:
            stmt = stmt.where(self._model.status == status)
        if priority:
            stmt = stmt.where(self._model.priority == priority)

        # Sort by work_rank (ascending = highest priority first)
        # If including unranked, put them at the end
        if include_unranked:
            stmt = stmt.order_by(
                self._model.work_rank.asc().nullslast(),
                self._model.priority.desc(),
                self._model.created_at.asc(),
            )
        else:
            stmt = stmt.order_by(self._model.work_rank.asc())

        if offset:
            stmt = stmt.offset(offset)
        if limit:
            stmt = stmt.limit(limit)

        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_next_issue(self) -> Issue | None:
        """Get the highest-ranked issue (work_rank=1) that is open or in_progress."""
        stmt = (
            select(self._model)
            .where(
                self._model.work_rank.isnot(None),
                self._model.status.in_(["open", "in_progress"]),
            )
            .order_by(self._model.work_rank.asc())
            .limit(1)
        )

        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_key(self, issue_key: str) -> Issue | None:
        """Get issue by its human-readable key (e.g., 'CNTXT-1')."""
        stmt = select(self._model).where(self._model.issue_key == issue_key)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()
