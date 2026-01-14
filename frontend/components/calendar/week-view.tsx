"use client";

import { useMemo } from "react";
import { format, startOfWeek, addDays, isSameDay, isToday, setHours } from "date-fns";
import { cn } from "@/lib/utils";
import type { CalendarEvent } from "@/lib/types";

interface WeekViewProps {
  currentDate: Date;
  events: CalendarEvent[];
  loading: boolean;
  onEventClick: (event: CalendarEvent) => void;
  onDateClick: (date: Date) => void;
}

export function WeekView({
  currentDate,
  events,
  loading,
  onEventClick,
  onDateClick,
}: WeekViewProps) {
  // Get days of the week
  const weekDays = useMemo(() => {
    const start = startOfWeek(currentDate);
    return Array.from({ length: 7 }, (_, i) => addDays(start, i));
  }, [currentDate]);

  // Hours to display
  const hours = Array.from({ length: 24 }, (_, i) => i);

  // Group events by date and hour
  const eventsByDateAndHour = useMemo(() => {
    const grouped = new Map<string, CalendarEvent[]>();
    events.forEach((event) => {
      const eventDate = new Date(event.date);
      const dateKey = format(eventDate, "yyyy-MM-dd");
      const hour = eventDate.getHours();
      const key = `${dateKey}-${hour}`;
      if (!grouped.has(key)) {
        grouped.set(key, []);
      }
      grouped.get(key)!.push(event);
    });
    return grouped;
  }, [events]);

  const getEventsForDateAndHour = (date: Date, hour: number) => {
    const dateKey = format(date, "yyyy-MM-dd");
    const key = `${dateKey}-${hour}`;
    return eventsByDateAndHour.get(key) || [];
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
    <div className="flex flex-col h-full overflow-hidden">
      {/* Header with days */}
      <div className="flex border-b bg-background sticky top-0 z-10">
        <div className="w-16 flex-shrink-0 border-r"></div>
        {weekDays.map((day) => {
          const isCurrentDay = isToday(day);
          return (
            <div
              key={day.toISOString()}
              className={cn(
                "flex-1 p-3 text-center border-r last:border-r-0",
                isCurrentDay && "bg-primary/5"
              )}
            >
              <div className="text-xs text-muted-foreground font-medium">
                {format(day, "EEE")}
              </div>
              <div
                className={cn(
                  "text-xl font-semibold mt-1",
                  isCurrentDay && "text-primary"
                )}
              >
                {format(day, "d")}
              </div>
            </div>
          );
        })}
      </div>

      {/* Time grid */}
      <div className="flex-1 overflow-auto">
        <div className="flex">
          {/* Time column */}
          <div className="w-16 flex-shrink-0 border-r">
            {hours.map((hour) => (
              <div
                key={hour}
                className="h-16 border-b text-xs text-muted-foreground text-right pr-2 pt-1"
              >
                {hour === 0 ? "12 AM" : hour < 12 ? `${hour} AM` : hour === 12 ? "12 PM" : `${hour - 12} PM`}
              </div>
            ))}
          </div>

          {/* Day columns */}
          {weekDays.map((day) => (
            <div key={day.toISOString()} className="flex-1 border-r last:border-r-0">
              {hours.map((hour) => {
                const hourEvents = getEventsForDateAndHour(day, hour);
                return (
                  <div
                    key={hour}
                    className="h-16 border-b p-1 cursor-pointer hover:bg-accent/30 transition-colors"
                    onClick={() => onDateClick(setHours(day, hour))}
                  >
                    {hourEvents.map((event) => (
                      <button
                        key={event.id}
                        onClick={(e) => {
                          e.stopPropagation();
                          onEventClick(event);
                        }}
                        className="w-full text-left px-1 py-0.5 rounded text-xs font-medium truncate mb-1 hover:opacity-80"
                        style={{
                          backgroundColor: event.color || "#3B82F6",
                          color: "white",
                        }}
                      >
                        <div className="flex items-center gap-1">
                          <span className="text-[10px]">{getEventIcon(event)}</span>
                          <span className="truncate">{event.title}</span>
                        </div>
                      </button>
                    ))}
                  </div>
                );
              })}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
