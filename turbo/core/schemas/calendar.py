"""Calendar event Pydantic schemas."""

from datetime import datetime
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class EventType(str, Enum):
    """Types of calendar events."""

    ISSUE = "issue"
    MILESTONE = "milestone"
    INITIATIVE = "initiative"
    PODCAST_EPISODE = "podcast_episode"
    LITERATURE = "literature"


class EventCategory(str, Enum):
    """Categories for visual grouping."""

    DEADLINE = "deadline"  # Due dates, target dates
    START = "start"  # Start dates
    RELEASE = "release"  # Published content
    OTHER = "other"


class CalendarEvent(BaseModel):
    """A single calendar event from any source."""

    # Core fields
    id: UUID
    title: str
    description: str | None = None
    date: datetime
    event_type: EventType
    category: EventCategory

    # Optional metadata
    status: str | None = None
    priority: str | None = None
    project_id: UUID | None = None
    project_name: str | None = None

    # URLs for navigation
    url: str | None = None

    # Display hints
    color: str | None = None
    icon: str | None = None

    model_config = ConfigDict(from_attributes=True)


class CalendarEventFilter(BaseModel):
    """Filters for calendar events."""

    start_date: datetime | None = None
    end_date: datetime | None = None
    event_types: list[EventType] | None = None
    categories: list[EventCategory] | None = None
    project_ids: list[UUID] | None = None
    statuses: list[str] | None = None
    priorities: list[str] | None = None


class CalendarEventsResponse(BaseModel):
    """Response containing calendar events."""

    events: list[CalendarEvent]
    total: int
    start_date: datetime | None = None
    end_date: datetime | None = None


class CalendarStats(BaseModel):
    """Statistics about calendar events."""

    total_events: int
    by_type: dict[str, int] = Field(default_factory=dict)
    by_category: dict[str, int] = Field(default_factory=dict)
    upcoming_count: int = 0  # Events in the next 7 days
    overdue_count: int = 0  # Past due dates for incomplete items
