"use client";

import { useMemo } from "react";
import { format, isToday, setHours } from "date-fns";
import { cn } from "@/lib/utils";
import type { CalendarEvent } from "@/lib/types";

interface DayViewProps {
  currentDate: Date;
  events: CalendarEvent[];
  loading: boolean;
  onEventClick: (event: CalendarEvent) => void;
  onDateClick: (date: Date) => void;
}

export function DayView({
  currentDate,
  events,
  loading,
  onEventClick,
  onDateClick,
}: DayViewProps) {
  // Hours to display
  const hours = Array.from({ length: 24 }, (_, i) => i);

  // Group events by hour
  const eventsByHour = useMemo(() => {
    const grouped = new Map<number, CalendarEvent[]>();
    events.forEach((event) => {
      const eventDate = new Date(event.date);
      const hour = eventDate.getHours();
      if (!grouped.has(hour)) {
        grouped.set(hour, []);
      }
      grouped.get(hour)!.push(event);
    });
    return grouped;
  }, [events]);

  const getEventsForHour = (hour: number) => {
    return eventsByHour.get(hour) || [];
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

  const isCurrentDay = isToday(currentDate);

  return (
    <div className="flex flex-col h-full overflow-hidden">
      {/* Header */}
      <div className={cn(
        "border-b p-4 bg-background sticky top-0 z-10",
        isCurrentDay && "bg-primary/5"
      )}>
        <div className="text-center">
          <div className="text-sm text-muted-foreground font-medium">
            {format(currentDate, "EEEE")}
          </div>
          <div className={cn(
            "text-3xl font-bold mt-1",
            isCurrentDay && "text-primary"
          )}>
            {format(currentDate, "d")}
          </div>
          <div className="text-sm text-muted-foreground">
            {format(currentDate, "MMMM yyyy")}
          </div>
        </div>
      </div>

      {/* Time slots */}
      <div className="flex-1 overflow-auto">
        {hours.map((hour) => {
          const hourEvents = getEventsForHour(hour);
          return (
            <div
              key={hour}
              className="flex border-b hover:bg-accent/30 transition-colors"
            >
              {/* Time label */}
              <div className="w-24 flex-shrink-0 p-3 text-sm text-muted-foreground text-right border-r">
                {hour === 0 ? "12:00 AM" : hour < 12 ? `${hour}:00 AM` : hour === 12 ? "12:00 PM" : `${hour - 12}:00 PM`}
              </div>

              {/* Events */}
              <div
                className="flex-1 p-3 min-h-[80px] cursor-pointer"
                onClick={() => onDateClick(setHours(currentDate, hour))}
              >
                <div className="space-y-2">
                  {hourEvents.map((event) => (
                    <button
                      key={event.id}
                      onClick={(e) => {
                        e.stopPropagation();
                        onEventClick(event);
                      }}
                      className="w-full text-left p-3 rounded-lg font-medium hover:opacity-90 transition-opacity shadow-sm"
                      style={{
                        backgroundColor: event.color || "#3B82F6",
                        color: "white",
                      }}
                    >
                      <div className="flex items-start justify-between gap-2">
                        <div className="flex-1">
                          <div className="flex items-center gap-2 mb-1">
                            <span className="text-sm">{getEventIcon(event)}</span>
                            <span className="font-semibold">{event.title}</span>
                          </div>
                          {event.description && (
                            <div className="text-sm opacity-90 line-clamp-2">
                              {event.description}
                            </div>
                          )}
                          <div className="text-xs opacity-80 mt-1">
                            {format(new Date(event.date), "h:mm a")}
                          </div>
                        </div>
                        {event.priority && (
                          <div className="text-xs font-bold px-2 py-1 bg-white/20 rounded">
                            {event.priority.toUpperCase()}
                          </div>
                        )}
                      </div>
                      {event.project_name && (
                        <div className="text-xs opacity-80 mt-2">
                          📁 {event.project_name}
                        </div>
                      )}
                    </button>
                  ))}
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {loading && (
        <div className="absolute inset-0 flex items-center justify-center bg-background/50">
          <div className="text-sm text-muted-foreground">Loading...</div>
        </div>
      )}
    </div>
  );
}
