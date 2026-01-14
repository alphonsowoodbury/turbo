"use client";

import { useState, useEffect } from "react";
import { CalendarView } from "@/components/calendar/calendar-view";
import { CalendarToolbar } from "@/components/calendar/calendar-toolbar";
import { EventModal } from "@/components/calendar/event-modal";
import type { CalendarEvent } from "@/lib/types";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8001";

export type ViewMode = "day" | "week" | "month" | "year";

export default function CalendarPage() {
  const [viewMode, setViewMode] = useState<ViewMode>("month");
  const [currentDate, setCurrentDate] = useState(new Date());
  const [events, setEvents] = useState<CalendarEvent[]>([]);
  const [loading, setLoading] = useState(false);
  const [selectedEvent, setSelectedEvent] = useState<CalendarEvent | null>(null);
  const [isEventModalOpen, setIsEventModalOpen] = useState(false);
  const [selectedDate, setSelectedDate] = useState<Date | null>(null);

  // Fetch events
  const fetchEvents = async (startDate: Date, endDate: Date) => {
    setLoading(true);
    try {
      const response = await fetch(
        `${API_BASE}/api/v1/calendar/events?` +
          `start_date=${startDate.toISOString()}&` +
          `end_date=${endDate.toISOString()}`
      );

      if (response.ok) {
        const data = await response.json();
        setEvents(data.events);
      }
    } catch (error) {
      console.error("Failed to fetch calendar events:", error);
    } finally {
      setLoading(false);
    }
  };

  // Handle creating a new event
  const handleCreateEvent = (date?: Date) => {
    setSelectedDate(date || currentDate);
    setSelectedEvent(null);
    setIsEventModalOpen(true);
  };

  // Handle editing an event
  const handleEditEvent = (event: CalendarEvent) => {
    setSelectedEvent(event);
    setIsEventModalOpen(true);
  };

  // Handle event save
  const handleEventSave = async () => {
    // Refresh events after save
    // Calculate date range based on current view
    const startDate = new Date(currentDate);
    startDate.setDate(1);
    const endDate = new Date(currentDate);
    endDate.setMonth(endDate.getMonth() + 1);
    await fetchEvents(startDate, endDate);
    setIsEventModalOpen(false);
  };

  return (
    <div className="h-screen flex flex-col bg-background">
      <CalendarToolbar
        viewMode={viewMode}
        currentDate={currentDate}
        onViewModeChange={setViewMode}
        onDateChange={setCurrentDate}
        onCreateEvent={() => handleCreateEvent()}
      />

      <div className="flex-1 overflow-hidden">
        <CalendarView
          viewMode={viewMode}
          currentDate={currentDate}
          events={events}
          loading={loading}
          onEventClick={handleEditEvent}
          onDateClick={handleCreateEvent}
          onDateChange={setCurrentDate}
          onFetchEvents={fetchEvents}
        />
      </div>

      {isEventModalOpen && (
        <EventModal
          event={selectedEvent}
          initialDate={selectedDate}
          isOpen={isEventModalOpen}
          onClose={() => setIsEventModalOpen(false)}
          onSave={handleEventSave}
        />
      )}
    </div>
  );
}
