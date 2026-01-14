"""Calendar Event API endpoints."""

from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from turbo.api.dependencies import get_db_session
from turbo.core.repositories.calendar_event import CalendarEventRepository
from turbo.core.schemas.calendar_event import (
    CalendarEventCreate,
    CalendarEventResponse,
    CalendarEventSummary,
    CalendarEventUpdate,
)

router = APIRouter()


def get_calendar_event_repo(
    session: AsyncSession = Depends(get_db_session),
) -> CalendarEventRepository:
    """Get calendar event repository dependency."""
    return CalendarEventRepository(session)


@router.post("/", response_model=CalendarEventResponse, status_code=status.HTTP_201_CREATED)
async def create_event(
    event_data: CalendarEventCreate,
    repo: CalendarEventRepository = Depends(get_calendar_event_repo),
) -> CalendarEventResponse:
    """Create a new calendar event."""
    event = await repo.create(event_data)
    return CalendarEventResponse.model_validate(event)


@router.get("/{event_id}", response_model=CalendarEventResponse)
async def get_event(
    event_id: UUID,
    repo: CalendarEventRepository = Depends(get_calendar_event_repo),
) -> CalendarEventResponse:
    """Get a calendar event by ID."""
    event = await repo.get_by_id(event_id)
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Calendar event with id {event_id} not found",
        )
    return CalendarEventResponse.model_validate(event)


@router.get("/", response_model=list[CalendarEventResponse])
async def get_events(
    category: str | None = Query(None),
    start_date: datetime | None = Query(None),
    end_date: datetime | None = Query(None),
    upcoming: bool = Query(False),
    include_completed: bool = Query(False),
    include_cancelled: bool = Query(False),
    limit: int | None = Query(100, ge=1, le=500),
    offset: int | None = Query(0, ge=0),
    repo: CalendarEventRepository = Depends(get_calendar_event_repo),
) -> list[CalendarEventResponse]:
    """Get all calendar events with optional filtering."""
    # Get upcoming events
    if upcoming:
        events = await repo.get_upcoming(
            limit=limit,
            include_completed=include_completed,
            include_cancelled=include_cancelled,
        )
    # Get by date range
    elif start_date and end_date:
        events = await repo.get_by_date_range(
            start_date=start_date,
            end_date=end_date,
            limit=limit,
            offset=offset,
        )
    # Get by category
    elif category:
        events = await repo.get_by_category(
            category=category,
            limit=limit,
            offset=offset,
        )
    # Get all
    else:
        events = await repo.get_all(limit=limit, offset=offset)

    return [CalendarEventResponse.model_validate(event) for event in events]


@router.put("/{event_id}", response_model=CalendarEventResponse)
async def update_event(
    event_id: UUID,
    event_data: CalendarEventUpdate,
    repo: CalendarEventRepository = Depends(get_calendar_event_repo),
) -> CalendarEventResponse:
    """Update a calendar event."""
    event = await repo.update(event_id, event_data)
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Calendar event with id {event_id} not found",
        )
    return CalendarEventResponse.model_validate(event)


@router.delete("/{event_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_event(
    event_id: UUID,
    repo: CalendarEventRepository = Depends(get_calendar_event_repo),
) -> None:
    """Delete a calendar event."""
    success = await repo.delete(event_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Calendar event with id {event_id} not found",
        )


@router.get("/recurring/", response_model=list[CalendarEventResponse])
async def get_recurring_events(
    limit: int | None = Query(100, ge=1, le=500),
    offset: int | None = Query(0, ge=0),
    repo: CalendarEventRepository = Depends(get_calendar_event_repo),
) -> list[CalendarEventResponse]:
    """Get recurring calendar events."""
    events = await repo.get_recurring(limit=limit, offset=offset)
    return [CalendarEventResponse.model_validate(event) for event in events]


@router.post("/{event_id}/complete", response_model=CalendarEventResponse)
async def mark_event_completed(
    event_id: UUID,
    repo: CalendarEventRepository = Depends(get_calendar_event_repo),
) -> CalendarEventResponse:
    """Mark a calendar event as completed."""
    event = await repo.mark_completed(event_id)
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Calendar event with id {event_id} not found",
        )
    return CalendarEventResponse.model_validate(event)


@router.post("/{event_id}/cancel", response_model=CalendarEventResponse)
async def mark_event_cancelled(
    event_id: UUID,
    repo: CalendarEventRepository = Depends(get_calendar_event_repo),
) -> CalendarEventResponse:
    """Mark a calendar event as cancelled."""
    event = await repo.mark_cancelled(event_id)
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Calendar event with id {event_id} not found",
        )
    return CalendarEventResponse.model_validate(event)
