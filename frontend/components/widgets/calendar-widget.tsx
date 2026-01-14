"use client";

import { useEffect, useState } from "react";
import { format, startOfMonth, endOfMonth, eachDayOfInterval, isSameMonth, isSameDay, isToday, addMonths, subMonths } from "date-fns";
import { ChevronLeft, ChevronRight, Circle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import type { CalendarEventsResponse, CalendarEvent } from "@/lib/types";
import Link from "next/link";
import { useWorkspace, getWorkspaceParams } from "@/hooks/use-workspace";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8001";

export function CalendarWidget() {
  const [currentMonth, setCurrentMonth] = useState(new Date());
  const [selectedDate, setSelectedDate] = useState<Date | null>(null);
  const [events, setEvents] = useState<CalendarEvent[]>([]);
  const [loading, setLoading] = useState(false);
  const { workspace, workCompany } = useWorkspace();

  // Fetch events for the current month
  useEffect(() => {
    const fetchEvents = async () => {
      setLoading(true);
      try {
        const start = startOfMonth(currentMonth);
        const end = endOfMonth(currentMonth);

        // Build workspace params
        const workspaceParams = getWorkspaceParams(workspace, workCompany);
        const queryParams = new URLSearchParams({
          start_date: start.toISOString(),
          end_date: end.toISOString(),
          ...workspaceParams,
        });

        const response = await fetch(
          `${API_BASE}/api/v1/calendar/events?${queryParams.toString()}`
        );

        if (response.ok) {
          const data: CalendarEventsResponse = await response.json();
          setEvents(data.events);
        }
      } catch (error) {
        console.error("Failed to fetch calendar events:", error);
      } finally {
        setLoading(false);
      }
    };

    fetchEvents();
  }, [currentMonth, workspace, workCompany]);

  const getEventsForDate = (date: Date) => {
    return events.filter((event) =>
      isSameDay(new Date(event.date), date)
    );
  };

  const getDaysInMonth = () => {
    const start = startOfMonth(currentMonth);
    const end = endOfMonth(currentMonth);
    return eachDayOfInterval({ start, end });
  };

  const displayedEvents = selectedDate
    ? getEventsForDate(selectedDate)
    : events
        .filter((e) => new Date(e.date) >= new Date())
        .sort((a, b) => new Date(a.date).getTime() - new Date(b.date).getTime())
        .slice(0, 5);

  const handleDateClick = (date: Date) => {
    if (getEventsForDate(date).length > 0) {
      setSelectedDate(isSameDay(date, selectedDate || new Date("1970-01-01")) ? null : date);
    }
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

  const days = getDaysInMonth();
  const firstDayOfWeek = startOfMonth(currentMonth).getDay();

  return (
    <div className="space-y-3">
      {/* Month Navigation */}
      <div className="flex items-center justify-between">
        <div className="text-sm font-medium">
          {format(currentMonth, "MMMM yyyy")}
        </div>
        <div className="flex items-center gap-1">
          <Button
            variant="ghost"
            size="sm"
            className="h-7 w-7 p-0"
            onClick={() => {
              setCurrentMonth(subMonths(currentMonth, 1));
              setSelectedDate(null);
            }}
          >
            <ChevronLeft className="h-4 w-4" />
          </Button>
          <Button
            variant="ghost"
            size="sm"
            className="h-7 w-7 p-0"
            onClick={() => {
              setCurrentMonth(addMonths(currentMonth, 1));
              setSelectedDate(null);
            }}
          >
            <ChevronRight className="h-4 w-4" />
          </Button>
        </div>
      </div>

      {/* Calendar Grid */}
      <div className="space-y-2">
        {/* Day headers */}
        <div className="grid grid-cols-7 gap-1 text-center">
          {["Su", "Mo", "Tu", "We", "Th", "Fr", "Sa"].map((day) => (
            <div key={day} className="text-[10px] font-medium text-muted-foreground">
              {day}
            </div>
          ))}
        </div>

        {/* Calendar days */}
        <div className="grid grid-cols-7 gap-1">
          {/* Empty cells for days before the month starts */}
          {Array.from({ length: firstDayOfWeek }).map((_, i) => (
            <div key={`empty-${i}`} />
          ))}

          {/* Actual days */}
          {days.map((day) => {
            const dayEvents = getEventsForDate(day);
            const hasEvents = dayEvents.length > 0;
            const isSelected = selectedDate && isSameDay(day, selectedDate);
            const isCurrentDay = isToday(day);

            return (
              <button
                key={day.toISOString()}
                onClick={() => handleDateClick(day)}
                className={cn(
                  "relative h-8 w-full rounded text-[11px] font-medium transition-colors",
                  "hover:bg-accent",
                  isCurrentDay && "bg-primary text-primary-foreground hover:bg-primary/90",
                  isSelected && "ring-2 ring-primary",
                  !isSameMonth(day, currentMonth) && "text-muted-foreground opacity-50",
                  hasEvents && "font-semibold"
                )}
                disabled={!hasEvents}
              >
                <span>{format(day, "d")}</span>
                {hasEvents && (
                  <div className="absolute bottom-0.5 left-1/2 -translate-x-1/2 flex gap-0.5">
                    {dayEvents.slice(0, 3).map((event, i) => (
                      <Circle
                        key={i}
                        className="h-1 w-1"
                        fill={event.color || "#3B82F6"}
                        color={event.color || "#3B82F6"}
                      />
                    ))}
                  </div>
                )}
              </button>
            );
          })}
        </div>
      </div>

      {/* Events List */}
      <div className="space-y-2">
        <div className="text-xs font-medium text-muted-foreground">
          {selectedDate
            ? `Events on ${format(selectedDate, "MMM d")}`
            : "Upcoming Events"}
        </div>

        {loading ? (
          <div className="text-xs text-muted-foreground">Loading...</div>
        ) : displayedEvents.length === 0 ? (
          <div className="text-xs text-muted-foreground">
            {selectedDate ? "No events on this day" : "No upcoming events"}
          </div>
        ) : (
          <div className="space-y-2">
            {displayedEvents.map((event) => (
              <Link
                key={event.id}
                href={event.url || "/calendar"}
                className="block"
              >
                <div
                  className="group rounded-md border p-2 hover:bg-accent transition-colors cursor-pointer"
                  style={{
                    borderLeftColor: event.color || "#3B82F6",
                    borderLeftWidth: "3px",
                  }}
                >
                  <div className="flex items-start justify-between gap-2">
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-1 mb-1">
                        <span className="text-xs">{getEventIcon(event)}</span>
                        <span className="text-xs font-medium truncate">
                          {event.title}
                        </span>
                      </div>
                      <div className="text-[10px] text-muted-foreground">
                        {format(new Date(event.date), "MMM d, h:mm a")}
                      </div>
                      {event.project_name && (
                        <Badge variant="outline" className="mt-1 text-[9px] h-4">
                          {event.project_name}
                        </Badge>
                      )}
                    </div>
                    {event.priority && (
                      <Badge
                        variant="outline"
                        className="text-[9px] h-4 shrink-0"
                        style={{
                          borderColor: event.color,
                          color: event.color,
                        }}
                      >
                        {event.priority}
                      </Badge>
                    )}
                  </div>
                </div>
              </Link>
            ))}
          </div>
        )}
      </div>

      {/* View Full Calendar Link */}
      <Link href="/calendar">
        <Button variant="outline" size="sm" className="w-full text-xs">
          View Full Calendar
        </Button>
      </Link>
    </div>
  );
}
