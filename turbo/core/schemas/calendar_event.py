"""Calendar Event Pydantic schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class CalendarEventBase(BaseModel):
    """Base calendar event schema with common fields."""

    title: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    start_date: datetime
    end_date: datetime | None = None
    all_day: bool = Field(default=False)
    location: str | None = Field(None, max_length=255)
    category: str = Field(
        default="other",
        pattern="^(personal|work|meeting|deadline|appointment|reminder|holiday|other)$"
    )
    color: str | None = Field(None, pattern="^#[0-9A-Fa-f]{6}$")
    is_recurring: bool = Field(default=False)
    recurrence_rule: str | None = Field(None, max_length=255)
    reminder_minutes: int | None = Field(None, ge=0)
    is_completed: bool = Field(default=False)
    is_cancelled: bool = Field(default=False)

    @field_validator("title")
    @classmethod
    def validate_title(cls, v: str) -> str:
        """Validate event title."""
        if not v.strip():
            raise ValueError("Title cannot be empty or whitespace")
        return v.strip()

    @field_validator("end_date")
    @classmethod
    def validate_end_date(cls, v: datetime | None, info) -> datetime | None:
        """Validate end date is after start date."""
        if v is not None and "start_date" in info.data:
            if v < info.data["start_date"]:
                raise ValueError("End date must be after start date")
        return v


class CalendarEventCreate(CalendarEventBase):
    """Schema for creating new calendar events."""

    pass


class CalendarEventUpdate(BaseModel):
    """Schema for updating calendar events (all fields optional)."""

    title: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = None
    start_date: datetime | None = None
    end_date: datetime | None = None
    all_day: bool | None = None
    location: str | None = Field(None, max_length=255)
    category: str | None = Field(
        None,
        pattern="^(personal|work|meeting|deadline|appointment|reminder|holiday|other)$"
    )
    color: str | None = Field(None, pattern="^#[0-9A-Fa-f]{6}$")
    is_recurring: bool | None = None
    recurrence_rule: str | None = Field(None, max_length=255)
    reminder_minutes: int | None = Field(None, ge=0)
    is_completed: bool | None = None
    is_cancelled: bool | None = None

    @field_validator("title")
    @classmethod
    def validate_title(cls, v: str | None) -> str | None:
        """Validate event title."""
        if v is not None and not v.strip():
            raise ValueError("Title cannot be empty or whitespace")
        return v.strip() if v else v

    @field_validator("end_date")
    @classmethod
    def validate_end_date(cls, v: datetime | None, info) -> datetime | None:
        """Validate end date is after start date."""
        if v is not None and "start_date" in info.data and info.data["start_date"] is not None:
            if v < info.data["start_date"]:
                raise ValueError("End date must be after start date")
        return v


class CalendarEventResponse(CalendarEventBase):
    """Schema for calendar event API responses."""

    id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CalendarEventSummary(BaseModel):
    """Summary information about a calendar event."""

    id: UUID
    title: str
    start_date: datetime
    end_date: datetime | None
    all_day: bool
    category: str
    color: str | None

    model_config = ConfigDict(from_attributes=True)
