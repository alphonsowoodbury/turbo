"""Company repository implementation for career management."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from turbo.core.models.company import Company
from turbo.core.repositories.base import BaseRepository
from turbo.core.schemas.company import CompanyCreate, CompanyUpdate


class CompanyRepository(BaseRepository[Company, CompanyCreate, CompanyUpdate]):
    """Repository for company data access."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, Company)

    async def get_by_target_status(self, target_status: str) -> list[Company]:
        """Get companies by target status."""
        stmt = select(self._model).where(self._model.target_status == target_status)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_by_industry(self, industry: str) -> list[Company]:
        """Get companies by industry."""
        stmt = select(self._model).where(self._model.industry == industry)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def search_by_name(self, name_pattern: str) -> list[Company]:
        """Search companies by name pattern."""
        stmt = select(self._model).where(self._model.name.ilike(f"%{name_pattern}%"))
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_target_companies(self) -> list[Company]:
        """Get companies in target statuses (researching, interested)."""
        stmt = select(self._model).where(
            self._model.target_status.in_(["researching", "interested"])
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_active_companies(self) -> list[Company]:
        """Get companies with active applications (applied, interviewing)."""
        stmt = select(self._model).where(
            self._model.target_status.in_(["applied", "interviewing"])
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_by_remote_policy(self, remote_policy: str) -> list[Company]:
        """Get companies by remote work policy."""
        stmt = select(self._model).where(self._model.remote_policy == remote_policy)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_with_all_relations(self, company_id: UUID) -> Company | None:
        """Get company with all relationships eagerly loaded."""
        stmt = (
            select(self._model)
            .where(self._model.id == company_id)
            .options(
                selectinload(self._model.job_applications),
                selectinload(self._model.network_contacts),
                selectinload(self._model.tags),
            )
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_with_applications(self, company_id: UUID) -> Company | None:
        """Get company with job applications eagerly loaded."""
        stmt = (
            select(self._model)
            .where(self._model.id == company_id)
            .options(selectinload(self._model.job_applications))
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_with_contacts(self, company_id: UUID) -> Company | None:
        """Get company with network contacts eagerly loaded."""
        stmt = (
            select(self._model)
            .where(self._model.id == company_id)
            .options(selectinload(self._model.network_contacts))
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()
