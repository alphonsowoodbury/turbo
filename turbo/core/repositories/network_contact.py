"""NetworkContact repository implementation for career management."""

from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from turbo.core.models.network_contact import NetworkContact
from turbo.core.repositories.base import BaseRepository
from turbo.core.schemas.network_contact import NetworkContactCreate, NetworkContactUpdate


class NetworkContactRepository(BaseRepository[NetworkContact, NetworkContactCreate, NetworkContactUpdate]):
    """Repository for network contact data access."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, NetworkContact)

    async def get_by_company(self, company_id: UUID) -> list[NetworkContact]:
        """Get network contacts by company ID."""
        stmt = select(self._model).where(self._model.company_id == company_id)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_by_contact_type(self, contact_type: str) -> list[NetworkContact]:
        """Get network contacts by type."""
        stmt = select(self._model).where(self._model.contact_type == contact_type)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_by_relationship_strength(self, strength: str) -> list[NetworkContact]:
        """Get network contacts by relationship strength."""
        stmt = select(self._model).where(self._model.relationship_strength == strength)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def search_by_name(self, name_pattern: str) -> list[NetworkContact]:
        """Search network contacts by name pattern (first or last name)."""
        search_pattern = f"%{name_pattern}%"
        stmt = select(self._model).where(
            (self._model.first_name.ilike(search_pattern)) |
            (self._model.last_name.ilike(search_pattern))
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def search_by_email(self, email_pattern: str) -> list[NetworkContact]:
        """Search network contacts by email pattern."""
        stmt = select(self._model).where(
            self._model.email.ilike(f"%{email_pattern}%")
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_recruiters(self) -> list[NetworkContact]:
        """Get all recruiter contacts (internal and external)."""
        stmt = select(self._model).where(
            self._model.contact_type.in_(["recruiter_internal", "recruiter_external"])
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_hiring_managers(self) -> list[NetworkContact]:
        """Get all hiring manager contacts."""
        stmt = select(self._model).where(self._model.contact_type == "hiring_manager")
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_referrers(self) -> list[NetworkContact]:
        """Get contacts who can provide referrals."""
        stmt = select(self._model).where(
            self._model.contact_type == "referrer"
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_active_contacts(self) -> list[NetworkContact]:
        """Get active network contacts."""
        stmt = select(self._model).where(self._model.is_active == True)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_warm_contacts(self) -> list[NetworkContact]:
        """Get warm and hot contacts."""
        stmt = select(self._model).where(
            self._model.relationship_strength.in_(["warm", "hot"])
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_contacts_needing_followup(self) -> list[NetworkContact]:
        """Get contacts with upcoming or overdue follow-ups."""
        now = datetime.now(timezone.utc)
        stmt = select(self._model).where(
            self._model.next_followup_date.isnot(None),
            self._model.next_followup_date <= now,
            self._model.is_active == True
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_by_referral_status(self, referral_status: str) -> list[NetworkContact]:
        """Get contacts by referral status."""
        stmt = select(self._model).where(self._model.referral_status == referral_status)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_with_all_relations(self, contact_id: UUID) -> NetworkContact | None:
        """Get network contact with all relationships eagerly loaded."""
        stmt = (
            select(self._model)
            .where(self._model.id == contact_id)
            .options(
                selectinload(self._model.company),
                selectinload(self._model.tags),
            )
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_with_company(self, contact_id: UUID) -> NetworkContact | None:
        """Get network contact with company eagerly loaded."""
        stmt = (
            select(self._model)
            .where(self._model.id == contact_id)
            .options(selectinload(self._model.company))
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()
