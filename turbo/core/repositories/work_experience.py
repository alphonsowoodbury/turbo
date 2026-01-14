"""Work experience repository."""

from typing import Optional, List
from uuid import UUID

from sqlalchemy import select, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from turbo.core.models.work_experience import WorkExperience, AchievementFact
from turbo.core.repositories.base import BaseRepository
from turbo.core.schemas.work_experience import (
    WorkExperienceCreate,
    WorkExperienceUpdate,
    AchievementFactCreate,
    AchievementFactUpdate,
)


class WorkExperienceRepository(BaseRepository[WorkExperience, WorkExperienceCreate, WorkExperienceUpdate]):
    """Repository for work experience CRUD operations."""

    def __init__(self, session: AsyncSession):
        super().__init__(session, WorkExperience)

    async def get_by_id_with_achievements(self, id: UUID) -> Optional[WorkExperience]:
        """Get work experience by ID with all achievements loaded."""
        stmt = (
            select(WorkExperience)
            .where(WorkExperience.id == id)
            .options(selectinload(WorkExperience.achievements))
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_company(
        self,
        company_id: UUID,
        limit: Optional[int] = None,
        offset: Optional[int] = None
    ) -> List[WorkExperience]:
        """Get all work experiences for a company."""
        stmt = (
            select(WorkExperience)
            .where(WorkExperience.company_id == company_id)
            .order_by(WorkExperience.start_date.desc())
        )

        if offset:
            stmt = stmt.offset(offset)
        if limit:
            stmt = stmt.limit(limit)

        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_current_experiences(
        self,
        limit: Optional[int] = None,
        offset: Optional[int] = None
    ) -> List[WorkExperience]:
        """Get all current work experiences."""
        stmt = (
            select(WorkExperience)
            .where(WorkExperience.is_current == True)
            .order_by(WorkExperience.start_date.desc())
        )

        if offset:
            stmt = stmt.offset(offset)
        if limit:
            stmt = stmt.limit(limit)

        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_by_employment_type(
        self,
        employment_type: str,
        limit: Optional[int] = None,
        offset: Optional[int] = None
    ) -> List[WorkExperience]:
        """Get work experiences by employment type."""
        stmt = (
            select(WorkExperience)
            .where(WorkExperience.employment_type == employment_type)
            .order_by(WorkExperience.start_date.desc())
        )

        if offset:
            stmt = stmt.offset(offset)
        if limit:
            stmt = stmt.limit(limit)

        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_all_with_achievements(
        self,
        limit: Optional[int] = None,
        offset: Optional[int] = None
    ) -> List[WorkExperience]:
        """Get all work experiences with achievements loaded."""
        stmt = (
            select(WorkExperience)
            .options(selectinload(WorkExperience.achievements))
            .order_by(WorkExperience.start_date.desc())
        )

        if offset:
            stmt = stmt.offset(offset)
        if limit:
            stmt = stmt.limit(limit)

        result = await self._session.execute(stmt)
        return list(result.scalars().all())


class AchievementFactRepository(BaseRepository[AchievementFact, AchievementFactCreate, AchievementFactUpdate]):
    """Repository for achievement fact CRUD operations."""

    def __init__(self, session: AsyncSession):
        super().__init__(session, AchievementFact)

    async def get_by_experience(
        self,
        experience_id: UUID,
        limit: Optional[int] = None,
        offset: Optional[int] = None
    ) -> List[AchievementFact]:
        """Get all achievements for a work experience."""
        stmt = (
            select(AchievementFact)
            .where(AchievementFact.experience_id == experience_id)
            .order_by(AchievementFact.display_order, AchievementFact.created_at)
        )

        if offset:
            stmt = stmt.offset(offset)
        if limit:
            stmt = stmt.limit(limit)

        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_by_metric_type(
        self,
        metric_type: str,
        limit: Optional[int] = None,
        offset: Optional[int] = None
    ) -> List[AchievementFact]:
        """Get achievements by metric type."""
        stmt = (
            select(AchievementFact)
            .where(AchievementFact.metric_type == metric_type)
            .order_by(AchievementFact.metric_value.desc().nullslast())
        )

        if offset:
            stmt = stmt.offset(offset)
        if limit:
            stmt = stmt.limit(limit)

        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_by_dimensions(
        self,
        dimensions: List[str],
        limit: Optional[int] = None,
        offset: Optional[int] = None
    ) -> List[AchievementFact]:
        """Get achievements that contain all specified dimensions."""
        stmt = select(AchievementFact)

        # Filter for achievements that contain all specified dimensions
        for dimension in dimensions:
            stmt = stmt.where(AchievementFact.dimensions.contains([dimension]))

        stmt = stmt.order_by(AchievementFact.created_at.desc())

        if offset:
            stmt = stmt.offset(offset)
        if limit:
            stmt = stmt.limit(limit)

        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_by_leadership_principles(
        self,
        principles: List[str],
        limit: Optional[int] = None,
        offset: Optional[int] = None
    ) -> List[AchievementFact]:
        """Get achievements that demonstrate specified leadership principles."""
        stmt = select(AchievementFact)

        # Filter for achievements that contain all specified principles
        for principle in principles:
            stmt = stmt.where(AchievementFact.leadership_principles.contains([principle]))

        stmt = stmt.order_by(AchievementFact.created_at.desc())

        if offset:
            stmt = stmt.offset(offset)
        if limit:
            stmt = stmt.limit(limit)

        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_by_skills(
        self,
        skills: List[str],
        limit: Optional[int] = None,
        offset: Optional[int] = None
    ) -> List[AchievementFact]:
        """Get achievements that used specified skills."""
        stmt = select(AchievementFact)

        # Filter for achievements that contain all specified skills
        for skill in skills:
            stmt = stmt.where(AchievementFact.skills_used.contains([skill]))

        stmt = stmt.order_by(AchievementFact.created_at.desc())

        if offset:
            stmt = stmt.offset(offset)
        if limit:
            stmt = stmt.limit(limit)

        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def search_by_text(
        self,
        query: str,
        limit: Optional[int] = None,
        offset: Optional[int] = None
    ) -> List[AchievementFact]:
        """Search achievements by fact_text, context, or impact using full-text search."""
        # PostgreSQL full-text search
        stmt = select(AchievementFact).where(
            or_(
                AchievementFact.fact_text.ilike(f"%{query}%"),
                AchievementFact.context.ilike(f"%{query}%"),
                AchievementFact.impact.ilike(f"%{query}%")
            )
        ).order_by(AchievementFact.created_at.desc())

        if offset:
            stmt = stmt.offset(offset)
        if limit:
            stmt = stmt.limit(limit)

        result = await self._session.execute(stmt)
        return list(result.scalars().all())
