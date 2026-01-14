"""Resume repository for database operations."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from turbo.core.models.resume import Resume, ResumeSection
from turbo.core.repositories.base import BaseRepository
from turbo.core.schemas.resume import ResumeCreate, ResumeUpdate, ResumeSectionCreate, ResumeSectionUpdate


class ResumeRepository(BaseRepository[Resume, ResumeCreate, ResumeUpdate]):
    """Repository for Resume CRUD operations."""

    def __init__(self, session: AsyncSession):
        """Initialize with database session."""
        super().__init__(session, Resume)

    async def get_with_sections(self, resume_id: UUID) -> Resume | None:
        """Get resume with all sections loaded."""
        result = await self._session.execute(
            select(Resume)
            .where(Resume.id == resume_id)
            .options(selectinload(Resume.sections))
        )
        return result.scalar_one_or_none()

    async def get_all_with_sections(
        self, skip: int = 0, limit: int = 100
    ) -> list[Resume]:
        """Get all resumes with sections loaded."""
        result = await self._session.execute(
            select(Resume)
            .options(selectinload(Resume.sections))
            .offset(skip)
            .limit(limit)
            .order_by(Resume.updated_at.desc())
        )
        return list(result.scalars().all())

    async def get_by_target_role(self, target_role: str) -> list[Resume]:
        """Get resumes filtered by target role."""
        result = await self._session.execute(
            select(Resume)
            .where(Resume.target_role == target_role)
            .options(selectinload(Resume.sections))
            .order_by(Resume.updated_at.desc())
        )
        return list(result.scalars().all())

    async def get_primary(self) -> Resume | None:
        """Get the primary resume."""
        result = await self._session.execute(
            select(Resume)
            .where(Resume.is_primary == True)  # noqa: E712
            .options(selectinload(Resume.sections))
        )
        return result.scalar_one_or_none()

    async def set_primary(self, resume_id: UUID) -> None:
        """Set a resume as primary (unsets all others)."""
        # Unset all primary flags
        await self._session.execute(
            select(Resume).where(Resume.is_primary == True)  # noqa: E712
        )
        resumes = (await self._session.execute(select(Resume))).scalars().all()
        for resume in resumes:
            resume.is_primary = False

        # Set the new primary
        resume = await self.get_by_id(resume_id)
        if resume:
            resume.is_primary = True
            await self._session.commit()


class ResumeSectionRepository(BaseRepository[ResumeSection, ResumeSectionCreate, ResumeSectionUpdate]):
    """Repository for ResumeSection CRUD operations."""

    def __init__(self, session: AsyncSession):
        """Initialize with database session."""
        super().__init__(session, ResumeSection)

    async def get_by_resume(self, resume_id: UUID) -> list[ResumeSection]:
        """Get all sections for a resume, ordered."""
        result = await self._session.execute(
            select(ResumeSection)
            .where(ResumeSection.resume_id == resume_id)
            .order_by(ResumeSection.order)
        )
        return list(result.scalars().all())

    async def get_active_sections(self, resume_id: UUID) -> list[ResumeSection]:
        """Get only active sections for a resume."""
        result = await self._session.execute(
            select(ResumeSection)
            .where(
                ResumeSection.resume_id == resume_id,
                ResumeSection.is_active == True,  # noqa: E712
            )
            .order_by(ResumeSection.order)
        )
        return list(result.scalars().all())

    async def reorder_sections(
        self, resume_id: UUID, section_orders: dict[UUID, int]
    ) -> None:
        """Update order of multiple sections."""
        for section_id, new_order in section_orders.items():
            section = await self.get_by_id(section_id)
            if section and section.resume_id == resume_id:
                section.order = new_order
        await self._session.commit()
