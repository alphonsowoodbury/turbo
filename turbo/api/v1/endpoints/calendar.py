"""Calendar API endpoints."""

from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from turbo.api.dependencies import get_db_session
from turbo.core.schemas.calendar import (
    CalendarEventsResponse,
    CalendarEventFilter,
    CalendarStats,
    EventType,
    EventCategory,
)
from turbo.core.services.calendar import CalendarService

router = APIRouter(prefix="/calendar", tags=["calendar"])


@router.get("/events", response_model=CalendarEventsResponse)
async def get_calendar_events(
    start_date: Annotated[datetime | None, Query(description="Start date for events")] = None,
    end_date: Annotated[datetime | None, Query(description="End date for events")] = None,
    event_types: Annotated[list[EventType] | None, Query(description="Filter by event types")] = None,
    categories: Annotated[list[EventCategory] | None, Query(description="Filter by categories")] = None,
    workspace: Annotated[str | None, Query(description="Filter by workspace", pattern="^(all|personal|freelance|work)$")] = None,
    work_company: Annotated[str | None, Query(description="Filter by work company")] = None,
    session: AsyncSession = Depends(get_db_session),
):
    """
    Get calendar events from all sources.

    Returns events from:
    - Issues (due dates)
    - Milestones (start and due dates)
    - Initiatives (start and target dates)
    - Podcast Episodes (published dates)
    - Literature (published dates)
    """
    service = CalendarService(session)

    # Build filter
    filter_params = CalendarEventFilter(
        start_date=start_date,
        end_date=end_date,
        event_types=event_types,
        categories=categories,
        workspace=workspace,
        work_company=work_company,
    )

    return await service.get_events(start_date, end_date, filter_params)


@router.get("/stats", response_model=CalendarStats)
async def get_calendar_stats(
    start_date: Annotated[datetime | None, Query(description="Start date for stats")] = None,
    end_date: Annotated[datetime | None, Query(description="End date for stats")] = None,
    session: AsyncSession = Depends(get_db_session),
):
    """
    Get statistics about calendar events.

    Includes:
    - Total event count
    - Events by type
    - Events by category
    - Upcoming events (next 7 days)
    - Overdue events
    """
    service = CalendarService(session)
    return await service.get_stats(start_date, end_date)
