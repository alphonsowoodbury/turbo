"""JobApplication repository implementation for career management."""

from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from turbo.core.models.job_application import JobApplication
from turbo.core.repositories.base import BaseRepository
from turbo.core.schemas.job_application import JobApplicationCreate, JobApplicationUpdate


class JobApplicationRepository(BaseRepository[JobApplication, JobApplicationCreate, JobApplicationUpdate]):
    """Repository for job application data access."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, JobApplication)

    async def get_by_company(self, company_id: UUID) -> list[JobApplication]:
        """Get job applications by company ID."""
        stmt = select(self._model).where(self._model.company_id == company_id)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_by_status(self, status: str) -> list[JobApplication]:
        """Get job applications by status."""
        stmt = select(self._model).where(self._model.status == status)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_by_source(self, source: str) -> list[JobApplication]:
        """Get job applications by source (LinkedIn, Indeed, etc.)."""
        stmt = select(self._model).where(self._model.source == source)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def search_by_job_title(self, title_pattern: str) -> list[JobApplication]:
        """Search job applications by job title pattern."""
        stmt = select(self._model).where(self._model.job_title.ilike(f"%{title_pattern}%"))
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_active_applications(self) -> list[JobApplication]:
        """Get applications in active statuses."""
        active_statuses = [
            "applied", "screening", "phone_screen",
            "technical_interview", "onsite", "offer", "negotiating"
        ]
        stmt = select(self._model).where(self._model.status.in_(active_statuses))
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_researching_applications(self) -> list[JobApplication]:
        """Get applications in research/interested status."""
        stmt = select(self._model).where(
            self._model.status.in_(["researching", "interested"])
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_completed_applications(self) -> list[JobApplication]:
        """Get applications in terminal statuses."""
        terminal_statuses = ["accepted", "rejected", "withdrawn", "ghosted"]
        stmt = select(self._model).where(self._model.status.in_(terminal_statuses))
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_applications_needing_followup(self) -> list[JobApplication]:
        """Get applications with upcoming or overdue follow-ups."""
        now = datetime.now(timezone.utc)
        stmt = select(self._model).where(
            self._model.next_followup_date.isnot(None),
            self._model.next_followup_date <= now,
            self._model.status.in_([
                "applied", "screening", "phone_screen",
                "technical_interview", "onsite"
            ])
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_by_resume(self, resume_id: UUID) -> list[JobApplication]:
        """Get applications by resume ID."""
        stmt = select(self._model).where(self._model.resume_id == resume_id)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_by_project(self, project_id: UUID) -> list[JobApplication]:
        """Get applications that reference a specific portfolio project."""
        stmt = select(self._model).where(self._model.project_id == project_id)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_with_all_relations(self, application_id: UUID) -> JobApplication | None:
        """Get job application with all relationships eagerly loaded."""
        stmt = (
            select(self._model)
            .where(self._model.id == application_id)
            .options(
                selectinload(self._model.company),
                selectinload(self._model.resume),
                selectinload(self._model.project),
                selectinload(self._model.cover_letter),
                selectinload(self._model.referrer),
                selectinload(self._model.tags),
            )
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_with_company(self, application_id: UUID) -> JobApplication | None:
        """Get job application with company eagerly loaded."""
        stmt = (
            select(self._model)
            .where(self._model.id == application_id)
            .options(selectinload(self._model.company))
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()
