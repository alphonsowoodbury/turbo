"""Repository for calendar event database operations."""

from datetime import datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from turbo.core.models.calendar_event import CalendarEvent
from turbo.core.repositories.base import BaseRepository
from turbo.core.schemas.calendar_event import CalendarEventCreate, CalendarEventUpdate


class CalendarEventRepository(
    BaseRepository[CalendarEvent, CalendarEventCreate, CalendarEventUpdate]
):
    """Repository for CalendarEvent operations."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, CalendarEvent)

    async def get_by_date_range(
        self,
        start_date: datetime,
        end_date: datetime,
        limit: int | None = None,
        offset: int | None = None,
        sort_by: str | None = None,
        sort_order: str = "desc",
    ) -> list[CalendarEvent]:
        """Get events within a date range."""
        stmt = select(CalendarEvent).where(
            CalendarEvent.start_date >= start_date,
            CalendarEvent.start_date <= end_date,
        )

        if sort_by and hasattr(CalendarEvent, sort_by):
            stmt = self._apply_sorting(stmt, sort_by, sort_order)
        else:
            stmt = stmt.order_by(CalendarEvent.start_date)

        if offset:
            stmt = stmt.offset(offset)
        if limit:
            stmt = stmt.limit(limit)

        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_by_category(
        self,
        category: str,
        limit: int | None = None,
        offset: int | None = None,
        sort_by: str | None = None,
        sort_order: str = "desc",
    ) -> list[CalendarEvent]:
        """Get events by category."""
        stmt = select(CalendarEvent).where(
            CalendarEvent.category == category
        )

        if sort_by and hasattr(CalendarEvent, sort_by):
            stmt = self._apply_sorting(stmt, sort_by, sort_order)
        else:
            stmt = stmt.order_by(CalendarEvent.start_date.desc())

        if offset:
            stmt = stmt.offset(offset)
        if limit:
            stmt = stmt.limit(limit)

        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_upcoming(
        self,
        limit: int | None = 10,
        include_completed: bool = False,
        include_cancelled: bool = False,
        sort_by: str | None = None,
        sort_order: str = "desc",
    ) -> list[CalendarEvent]:
        """Get upcoming events."""
        stmt = select(CalendarEvent).where(
            CalendarEvent.start_date >= datetime.utcnow()
        )

        if not include_completed:
            stmt = stmt.where(CalendarEvent.is_completed == False)
        if not include_cancelled:
            stmt = stmt.where(CalendarEvent.is_cancelled == False)

        if sort_by and hasattr(CalendarEvent, sort_by):
            stmt = self._apply_sorting(stmt, sort_by, sort_order)
        else:
            stmt = stmt.order_by(CalendarEvent.start_date)

        if limit:
            stmt = stmt.limit(limit)

        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_recurring(
        self,
        limit: int | None = None,
        offset: int | None = None,
    ) -> list[CalendarEvent]:
        """Get recurring events."""
        stmt = select(CalendarEvent).where(
            CalendarEvent.is_recurring == True
        ).order_by(CalendarEvent.start_date)

        if offset:
            stmt = stmt.offset(offset)
        if limit:
            stmt = stmt.limit(limit)

        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def mark_completed(self, id: UUID) -> CalendarEvent | None:
        """Mark an event as completed."""
        event = await self.get_by_id(id)
        if not event:
            return None

        event.is_completed = True
        await self._session.commit()
        await self._session.refresh(event)
        return event

    async def mark_cancelled(self, id: UUID) -> CalendarEvent | None:
        """Mark an event as cancelled."""
        event = await self.get_by_id(id)
        if not event:
            return None

        event.is_cancelled = True
        await self._session.commit()
        await self._session.refresh(event)
        return event
