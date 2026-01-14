"""Staff repository for data access operations."""

from typing import Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from turbo.core.models.staff import Staff
from turbo.core.repositories.base import BaseRepository


class StaffRepository(BaseRepository[Staff, dict, dict]):
    """Repository for Staff model with custom query methods."""

    def __init__(self, session: AsyncSession):
        super().__init__(session, Staff)

    async def get_by_id_with_relationships(self, staff_id: UUID) -> Optional[Staff]:
        """
        Get staff by ID with eagerly loaded relationships.

        This method loads the review_requests relationship eagerly to avoid
        lazy loading issues in async contexts.

        Args:
            staff_id: Staff UUID

        Returns:
            Staff instance with relationships loaded, or None if not found
        """
        stmt = (
            select(Staff)
            .where(Staff.id == staff_id)
            .options(selectinload(Staff.review_requests))
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_handle(self, handle: str) -> Optional[Staff]:
        """
        Get staff by unique handle or alias.

        This method checks both handle and alias fields to support
        both formal handles (e.g., "ChiefOfStaff") and short aliases
        (e.g., "Chief") for @ mentions.

        Args:
            handle: Staff handle or alias (e.g., "ChiefOfStaff" or "Chief")

        Returns:
            Staff instance or None if not found
        """
        stmt = select(Staff).where(
            (Staff.handle == handle) | (Staff.alias == handle)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_leadership_staff(self) -> list[Staff]:
        """
        Get all active leadership staff.

        Leadership staff have universal edit permissions.

        Returns:
            List of active leadership staff members
        """
        stmt = (
            select(Staff)
            .where(Staff.is_leadership_role == True, Staff.is_active == True)
            .order_by(Staff.name)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_domain_staff(self) -> list[Staff]:
        """
        Get all active domain expert staff.

        Domain staff can only edit what they're assigned.

        Returns:
            List of active domain expert staff members
        """
        stmt = (
            select(Staff)
            .where(Staff.is_leadership_role == False, Staff.is_active == True)
            .order_by(Staff.name)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_active_staff(self, role_type: Optional[str] = None) -> list[Staff]:
        """
        Get all active staff with optional role type filter.

        Args:
            role_type: Optional filter by role_type (leadership|domain_expert)

        Returns:
            List of active staff members
        """
        stmt = select(Staff).where(Staff.is_active == True)

        if role_type:
            stmt = stmt.where(Staff.role_type == role_type)

        stmt = stmt.order_by(Staff.name)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_by_monitoring_scope(
        self, entity_type: str, tags: Optional[list[str]] = None
    ) -> list[Staff]:
        """
        Get staff that monitor a specific entity type or tags.

        Args:
            entity_type: Entity type to monitor (issue, initiative, milestone, project)
            tags: Optional list of tags to match

        Returns:
            List of staff members monitoring this scope
        """
        # Use JSONB query to find staff monitoring this entity type
        stmt = (
            select(Staff)
            .where(
                Staff.is_active == True,
                Staff.monitoring_scope["entity_types"]
                .astext.cast(str)
                .contains(entity_type),
            )
            .order_by(Staff.name)
        )

        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def search_by_name_or_handle(self, query: str) -> list[Staff]:
        """
        Search staff by name, handle, or alias.

        Args:
            query: Search query string

        Returns:
            List of matching staff members
        """
        search = f"%{query}%"
        stmt = (
            select(Staff)
            .where(
                (Staff.name.ilike(search))
                | (Staff.handle.ilike(search))
                | (Staff.alias.ilike(search)),
                Staff.is_active == True,
            )
            .order_by(Staff.name)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())
