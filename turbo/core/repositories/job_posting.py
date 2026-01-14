"""Repository for job posting data access."""

from typing import Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from turbo.core.models.job_posting import JobPosting, SearchCriteria, JobSearchHistory
from turbo.core.repositories.base import BaseRepository
from turbo.core.schemas.job_posting import (
    JobPostingCreate,
    JobPostingUpdate,
    SearchCriteriaCreate,
    SearchCriteriaUpdate,
    JobSearchHistoryCreate,
)


class JobPostingRepository(BaseRepository[JobPosting, JobPostingCreate, JobPostingUpdate]):
    """Repository for job posting operations."""

    def __init__(self, session: AsyncSession):
        super().__init__(session, JobPosting)

    async def get_by_status(self, status: str, limit: int = 100, offset: int = 0) -> list[JobPosting]:
        """Get job postings by status."""
        stmt = (
            select(JobPosting)
            .where(JobPosting.status == status)
            .order_by(JobPosting.discovered_date.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_by_source(self, source: str, limit: int = 100, offset: int = 0) -> list[JobPosting]:
        """Get job postings by source."""
        stmt = (
            select(JobPosting)
            .where(JobPosting.source == source)
            .order_by(JobPosting.discovered_date.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_by_min_score(
        self, min_score: float, limit: int = 100, offset: int = 0
    ) -> list[JobPosting]:
        """Get job postings with minimum match score."""
        stmt = (
            select(JobPosting)
            .where(JobPosting.match_score >= min_score)
            .order_by(JobPosting.match_score.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_by_external_id(self, source: str, external_id: str) -> Optional[JobPosting]:
        """Get job posting by source and external ID."""
        stmt = select(JobPosting).where(
            JobPosting.source == source, JobPosting.external_id == external_id
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_new_jobs(self, limit: int = 100) -> list[JobPosting]:
        """Get all new (unreviewed) job postings."""
        return await self.get_by_status("new", limit=limit)


class SearchCriteriaRepository(
    BaseRepository[SearchCriteria, SearchCriteriaCreate, SearchCriteriaUpdate]
):
    """Repository for search criteria operations."""

    def __init__(self, session: AsyncSession):
        super().__init__(session, SearchCriteria)

    async def get_active_criteria(self) -> list[SearchCriteria]:
        """Get all active search criteria."""
        stmt = select(SearchCriteria).where(SearchCriteria.is_active == True)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_criteria_needing_search(self) -> list[SearchCriteria]:
        """Get active criteria that need to be searched now."""
        from datetime import datetime

        stmt = select(SearchCriteria).where(
            SearchCriteria.is_active == True,
            SearchCriteria.auto_search_enabled == True,
            SearchCriteria.next_search_at <= datetime.now(),
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())


class JobSearchHistoryRepository(BaseRepository[JobSearchHistory, JobSearchHistoryCreate, dict]):
    """Repository for job search history operations."""

    def __init__(self, session: AsyncSession):
        super().__init__(session, JobSearchHistory)

    async def get_by_criteria(
        self, criteria_id: UUID, limit: int = 100
    ) -> list[JobSearchHistory]:
        """Get search history for a criteria."""
        stmt = (
            select(JobSearchHistory)
            .where(JobSearchHistory.search_criteria_id == criteria_id)
            .order_by(JobSearchHistory.created_at.desc())
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_recent_searches(self, limit: int = 50) -> list[JobSearchHistory]:
        """Get recent search history."""
        stmt = (
            select(JobSearchHistory).order_by(JobSearchHistory.created_at.desc()).limit(limit)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())
