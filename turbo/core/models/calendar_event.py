"""Calendar Event model for standalone events."""

from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from turbo.core.models.base import Base


class CalendarEvent(Base):
    """Calendar Event model for standalone events not tied to other entities."""

    __tablename__ = "calendar_events"

    # Basic fields
    title: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Date and time
    start_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    end_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    all_day: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Location
    location: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Categorization
    category: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="other",
        index=True
    )  # personal, work, meeting, deadline, appointment, reminder, holiday, other

    color: Mapped[Optional[str]] = mapped_column(String(7), nullable=True)  # Hex color code

    # Recurrence (basic support)
    is_recurring: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    recurrence_rule: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)  # RRULE format

    # Reminders
    reminder_minutes: Mapped[Optional[int]] = mapped_column(nullable=True)  # Minutes before event

    # Status
    is_completed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_cancelled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    def __repr__(self) -> str:
        """String representation."""
        return f"<CalendarEvent {self.title} on {self.start_date}>"
