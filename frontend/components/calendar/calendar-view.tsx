"use client";

import { useEffect } from "react";
import { startOfMonth, endOfMonth, startOfWeek, endOfWeek, startOfYear, endOfYear, addDays } from "date-fns";
import { MonthView } from "./month-view";
import { WeekView } from "./week-view";
import { DayView } from "./day-view";
import { YearView } from "./year-view";
import type { ViewMode } from "@/app/calendar/page";
import type { CalendarEvent } from "@/lib/types";

interface CalendarViewProps {
  viewMode: ViewMode;
  currentDate: Date;
  events: CalendarEvent[];
  loading: boolean;
  onEventClick: (event: CalendarEvent) => void;
  onDateClick: (date: Date) => void;
  onDateChange: (date: Date) => void;
  onFetchEvents: (startDate: Date, endDate: Date) => void;
}

export function CalendarView({
  viewMode,
  currentDate,
  events,
  loading,
  onEventClick,
  onDateClick,
  onDateChange,
  onFetchEvents,
}: CalendarViewProps) {
  // Fetch events when view or date changes
  useEffect(() => {
    let startDate: Date;
    let endDate: Date;

    switch (viewMode) {
      case "day":
        startDate = new Date(currentDate);
        startDate.setHours(0, 0, 0, 0);
        endDate = new Date(currentDate);
        endDate.setHours(23, 59, 59, 999);
        break;
      case "week":
        startDate = startOfWeek(currentDate);
        endDate = endOfWeek(currentDate);
        break;
      case "month":
        // Get a bit more than the month to show events in adjacent weeks
        startDate = startOfWeek(startOfMonth(currentDate));
        endDate = endOfWeek(endOfMonth(currentDate));
        break;
      case "year":
        startDate = startOfYear(currentDate);
        endDate = endOfYear(currentDate);
        break;
    }

    onFetchEvents(startDate, endDate);
  }, [viewMode, currentDate, onFetchEvents]);

  const commonProps = {
    currentDate,
    events,
    loading,
    onEventClick,
    onDateClick,
    onDateChange,
  };

  switch (viewMode) {
    case "day":
      return <DayView {...commonProps} />;
    case "week":
      return <WeekView {...commonProps} />;
    case "month":
      return <MonthView {...commonProps} />;
    case "year":
      return <YearView {...commonProps} />;
  }
}
