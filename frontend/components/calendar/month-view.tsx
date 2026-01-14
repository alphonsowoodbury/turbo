"use client";

import { useMemo } from "react";
import { format, isSameMonth, isSameDay, isToday, startOfMonth, endOfMonth, startOfWeek, endOfWeek, eachDayOfInterval } from "date-fns";
import { cn } from "@/lib/utils";
import type { CalendarEvent } from "@/lib/types";

interface MonthViewProps {
  currentDate: Date;
  events: CalendarEvent[];
  loading: boolean;
  onEventClick: (event: CalendarEvent) => void;
  onDateClick: (date: Date) => void;
}

export function MonthView({
  currentDate,
  events,
  loading,
  onEventClick,
  onDateClick,
}: MonthViewProps) {
  // Get all days to display in the month grid
  const days = useMemo(() => {
    const start = startOfWeek(startOfMonth(currentDate));
    const end = endOfWeek(endOfMonth(currentDate));
    return eachDayOfInterval({ start, end });
  }, [currentDate]);

  // Group events by date
  const eventsByDate = useMemo(() => {
    const grouped = new Map<string, CalendarEvent[]>();
    events.forEach((event) => {
      const dateKey = format(new Date(event.date), "yyyy-MM-dd");
      if (!grouped.has(dateKey)) {
        grouped.set(dateKey, []);
      }
      grouped.get(dateKey)!.push(event);
    });
    return grouped;
  }, [events]);

  const getEventsForDay = (date: Date) => {
    const dateKey = format(date, "yyyy-MM-dd");
    return eventsByDate.get(dateKey) || [];
  };

  const getEventIcon = (event: CalendarEvent) => {
    switch (event.event_type) {
      case "issue":
        return "📋";
      case "milestone":
        return "🎯";
      case "initiative":
        return "🚀";
      case "podcast_episode":
        return "🎙️";
      case "literature":
        return "📚";
      default:
        return "📅";
    }
  };

  return (
    <div className="flex flex-col h-full bg-background">
      {/* Week day headers */}
      <div className="grid grid-cols-7 border-b bg-muted/50">
        {["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"].map((day) => (
          <div
            key={day}
            className="p-2 text-center text-sm font-medium text-muted-foreground border-r last:border-r-0"
          >
            {day}
          </div>
        ))}
      </div>

      {/* Calendar grid */}
      <div className="flex-1 grid grid-cols-7 auto-rows-fr overflow-auto">
        {days.map((day) => {
          const dayEvents = getEventsForDay(day);
          const isCurrentMonth = isSameMonth(day, currentDate);
          const isCurrentDay = isToday(day);
          const maxVisibleEvents = 4; // Show max 4 events, then "+X more"
          const visibleEvents = dayEvents.slice(0, maxVisibleEvents);
          const hiddenCount = Math.max(0, dayEvents.length - maxVisibleEvents);

          return (
            <div
              key={day.toISOString()}
              className={cn(
                "border-r border-b last:border-r-0 p-2 min-h-[120px] cursor-pointer hover:bg-accent/50 transition-colors",
                !isCurrentMonth && "bg-muted/20"
              )}
              onClick={() => onDateClick(day)}
            >
              {/* Day number */}
              <div className="flex items-center justify-between mb-1">
                <div
                  className={cn(
                    "flex h-7 w-7 items-center justify-center rounded-full text-sm font-medium",
                    isCurrentDay && "bg-primary text-primary-foreground",
                    !isCurrentDay && !isCurrentMonth && "text-muted-foreground"
                  )}
                >
                  {format(day, "d")}
                </div>
              </div>

              {/* Events */}
              <div className="space-y-1">
                {visibleEvents.map((event) => (
                  <button
                    key={event.id}
                    onClick={(e) => {
                      e.stopPropagation();
                      onEventClick(event);
                    }}
                    className={cn(
                      "w-full text-left px-2 py-0.5 rounded text-xs font-medium truncate hover:opacity-80 transition-opacity",
                      "flex items-center gap-1"
                    )}
                    style={{
                      backgroundColor: event.color ? `${event.color}20` : "#3B82F620",
                      borderLeft: `3px solid ${event.color || "#3B82F6"}`,
                    }}
                  >
                    <span className="text-[10px]">{getEventIcon(event)}</span>
                    <span className="truncate">{event.title}</span>
                  </button>
                ))}

                {hiddenCount > 0 && (
                  <div className="px-2 text-xs text-muted-foreground font-medium">
                    +{hiddenCount} more
                  </div>
                )}
              </div>

              {/* Loading indicator */}
              {loading && dayEvents.length === 0 && (
                <div className="text-xs text-muted-foreground">Loading...</div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
