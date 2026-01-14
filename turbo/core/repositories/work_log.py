"""Work Log repository implementation."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from turbo.core.models.work_log import WorkLog
from turbo.core.repositories.base import BaseRepository
from turbo.core.schemas.work_log import WorkLogCreate, WorkLogUpdate


class WorkLogRepository(BaseRepository[WorkLog, WorkLogCreate, WorkLogUpdate]):
    """Repository for work log data access."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, WorkLog)

    async def get_by_issue(self, issue_id: UUID) -> list[WorkLog]:
        """Get all work logs for an issue."""
        stmt = select(self._model).where(self._model.issue_id == issue_id).order_by(self._model.started_at.desc())
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_active_work_log(self, issue_id: UUID) -> WorkLog | None:
        """Get the active (not ended) work log for an issue."""
        stmt = (
            select(self._model)
            .where(self._model.issue_id == issue_id)
            .where(self._model.ended_at.is_(None))
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_started_by(self, started_by: str) -> list[WorkLog]:
        """Get work logs by who started them."""
        stmt = select(self._model).where(self._model.started_by == started_by).order_by(self._model.started_at.desc())
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_active_work_logs(self) -> list[WorkLog]:
        """Get all active work logs."""
        stmt = select(self._model).where(self._model.ended_at.is_(None)).order_by(self._model.started_at.desc())
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_completed_work_logs(self, issue_id: UUID) -> list[WorkLog]:
        """Get all completed work logs for an issue."""
        stmt = (
            select(self._model)
            .where(self._model.issue_id == issue_id)
            .where(self._model.ended_at.isnot(None))
            .order_by(self._model.ended_at.desc())
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())
