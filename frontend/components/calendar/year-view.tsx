"use client";

import { useMemo } from "react";
import { format, startOfMonth, endOfMonth, startOfWeek, endOfWeek, eachDayOfInterval, isSameMonth, isSameDay, isToday, setMonth } from "date-fns";
import { cn } from "@/lib/utils";
import type { CalendarEvent } from "@/lib/types";

interface YearViewProps {
  currentDate: Date;
  events: CalendarEvent[];
  loading: boolean;
  onDateClick: (date: Date) => void;
  onDateChange: (date: Date) => void;
}

export function YearView({
  currentDate,
  events,
  loading,
  onDateClick,
  onDateChange,
}: YearViewProps) {
  // Generate all 12 months
  const months = Array.from({ length: 12 }, (_, i) => setMonth(currentDate, i));

  // Count events by date
  const eventCountByDate = useMemo(() => {
    const counts = new Map<string, number>();
    events.forEach((event) => {
      const dateKey = format(new Date(event.date), "yyyy-MM-dd");
      counts.set(dateKey, (counts.get(dateKey) || 0) + 1);
    });
    return counts;
  }, [events]);

  const getEventCount = (date: Date) => {
    const dateKey = format(date, "yyyy-MM-dd");
    return eventCountByDate.get(dateKey) || 0;
  };

  return (
    <div className="h-full overflow-auto p-6 bg-background">
      <div className="max-w-7xl mx-auto">
        {/* Year title */}
        <h2 className="text-3xl font-bold text-center mb-8">
          {format(currentDate, "yyyy")}
        </h2>

        {/* Grid of months */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
          {months.map((month, monthIndex) => {
            const monthStart = startOfMonth(month);
            const monthEnd = endOfMonth(month);
            const calendarStart = startOfWeek(monthStart);
            const calendarEnd = endOfWeek(monthEnd);
            const days = eachDayOfInterval({ start: calendarStart, end: calendarEnd });

            return (
              <div
                key={monthIndex}
                className="border rounded-lg p-4 bg-card hover:shadow-lg transition-shadow cursor-pointer"
                onClick={() => onDateChange(month)}
              >
                {/* Month name */}
                <h3 className="text-center font-semibold mb-3">
                  {format(month, "MMMM")}
                </h3>

                {/* Day headers */}
                <div className="grid grid-cols-7 gap-1 mb-2">
                  {["S", "M", "T", "W", "T", "F", "S"].map((day, i) => (
                    <div
                      key={i}
                      className="text-center text-xs text-muted-foreground font-medium"
                    >
                      {day}
                    </div>
                  ))}
                </div>

                {/* Days */}
                <div className="grid grid-cols-7 gap-1">
                  {days.map((day) => {
                    const isInMonth = isSameMonth(day, month);
                    const isCurrentDay = isToday(day);
                    const eventCount = getEventCount(day);
                    const hasEvents = eventCount > 0;

                    return (
                      <button
                        key={day.toISOString()}
                        onClick={(e) => {
                          e.stopPropagation();
                          onDateClick(day);
                        }}
                        className={cn(
                          "aspect-square text-xs rounded flex flex-col items-center justify-center relative",
                          "hover:bg-accent transition-colors",
                          !isInMonth && "text-muted-foreground opacity-40",
                          isCurrentDay && "bg-primary text-primary-foreground font-bold",
                          hasEvents && isInMonth && !isCurrentDay && "font-semibold"
                        )}
                      >
                        <span>{format(day, "d")}</span>
                        {hasEvents && (
                          <div className="absolute bottom-0.5 flex gap-0.5">
                            {Array.from({ length: Math.min(eventCount, 3) }).map((_, i) => (
                              <div
                                key={i}
                                className={cn(
                                  "w-1 h-1 rounded-full",
                                  isCurrentDay ? "bg-primary-foreground" : "bg-primary"
                                )}
                              />
                            ))}
                          </div>
                        )}
                      </button>
                    );
                  })}
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {loading && (
        <div className="absolute inset-0 flex items-center justify-center bg-background/50">
          <div className="text-sm text-muted-foreground">Loading...</div>
        </div>
      )}
    </div>
  );
}
