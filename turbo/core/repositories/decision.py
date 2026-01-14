"""Decision repository implementation."""

from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from turbo.core.models.decision import Decision
from turbo.core.repositories.base import BaseRepository
from turbo.core.schemas.decision import DecisionCreate, DecisionUpdate


class DecisionRepository(BaseRepository[Decision, DecisionCreate, DecisionUpdate]):
    """Repository for decision data access."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, Decision)

    async def get_by_key(self, decision_key: str) -> Decision | None:
        """Get decision by its key (e.g., 'DEC-1')."""
        stmt = select(self._model).where(self._model.decision_key == decision_key)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_status(self, status: str) -> list[Decision]:
        """Get decisions by status."""
        stmt = (
            select(self._model)
            .options(selectinload(self._model.initiatives))
            .where(self._model.status == status)
            .order_by(self._model.created_at.desc())
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_by_type(self, decision_type: str) -> list[Decision]:
        """Get decisions by type."""
        stmt = (
            select(self._model)
            .options(selectinload(self._model.initiatives))
            .where(self._model.decision_type == decision_type)
            .order_by(self._model.created_at.desc())
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_with_initiatives(self, id: UUID) -> Decision | None:
        """Get decision with its initiatives loaded."""
        stmt = (
            select(self._model)
            .options(selectinload(self._model.initiatives))
            .where(self._model.id == id)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_all_with_relations(
        self, limit: int | None = None, offset: int | None = None
    ) -> list[Decision]:
        """Get all decisions with relations loaded."""
        stmt = (
            select(self._model)
            .options(selectinload(self._model.initiatives))
            .order_by(self._model.created_at.desc())
        )
        if limit is not None:
            stmt = stmt.limit(limit)
        if offset is not None:
            stmt = stmt.offset(offset)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def approve(self, id: UUID, decided_by: str | None = None) -> Decision | None:
        """Approve a decision."""
        decision = await self.get(id)
        if not decision:
            return None

        decision.status = "approved"
        decision.decided_at = datetime.now(timezone.utc)
        if decided_by:
            decision.decided_by = decided_by

        await self._session.commit()
        await self._session.refresh(decision)
        return decision

    async def supersede(
        self, id: UUID, superseded_by_id: UUID
    ) -> Decision | None:
        """Mark a decision as superseded by another."""
        decision = await self.get(id)
        if not decision:
            return None

        decision.status = "superseded"
        decision.superseded_at = datetime.now(timezone.utc)
        decision.superseded_by_id = superseded_by_id

        await self._session.commit()
        await self._session.refresh(decision)
        return decision

    async def get_next_key_number(self) -> int:
        """Get the next decision number for key generation."""
        stmt = select(func.max(
            func.cast(
                func.substr(self._model.decision_key, 5),
                type_=int
            )
        )).where(self._model.decision_key.isnot(None))
        result = await self._session.execute(stmt)
        max_num = result.scalar()
        return (max_num or 0) + 1

    async def count(self) -> int:
        """Get total count of decisions."""
        stmt = select(func.count()).select_from(self._model)
        result = await self._session.execute(stmt)
        return result.scalar() or 0
