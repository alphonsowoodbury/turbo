"use client";

import { useState, useEffect } from "react";
import { format } from "date-fns";
import { X, Calendar, Clock, AlertCircle, Link2, CalendarDays, MapPin } from "lucide-react";
import { cn } from "@/lib/utils";
import { calendarEventsApi } from "@/lib/api/calendar-events";
import type { CalendarEvent, EventType, StandaloneEventCategory } from "@/lib/types";

interface EventModalProps {
  event: CalendarEvent | null;
  initialDate: Date | null;
  isOpen: boolean;
  onClose: () => void;
  onSave: (eventData?: Partial<CalendarEvent>) => Promise<void>;
}

type EventMode = "standalone" | "linked";

type StandaloneFormData = {
  title: string;
  description: string;
  start_date: string;
  start_time: string;
  end_date: string;
  end_time: string;
  all_day: boolean;
  location: string;
  category: StandaloneEventCategory;
  color: string;
  reminder_minutes: string;
};

type LinkedFormData = {
  title: string;
  description: string;
  date: string;
  time: string;
  event_type: EventType;
  priority: "low" | "medium" | "high" | "critical" | "";
  status: string;
  project_id: string;
};

export function EventModal({ event, initialDate, isOpen, onClose, onSave }: EventModalProps) {
  const [mode, setMode] = useState<EventMode>("standalone");
  const [standaloneForm, setStandaloneForm] = useState<StandaloneFormData>({
    title: "",
    description: "",
    start_date: "",
    start_time: "",
    end_date: "",
    end_time: "",
    all_day: false,
    location: "",
    category: "other",
    color: "#3B82F6",
    reminder_minutes: "",
  });
  const [linkedForm, setLinkedForm] = useState<LinkedFormData>({
    title: "",
    description: "",
    date: "",
    time: "",
    event_type: "issue",
    priority: "",
    status: "open",
    project_id: "",
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Initialize form data
  useEffect(() => {
    if (event) {
      // Edit mode - only supports linked events for now
      setMode("linked");
      const eventDate = new Date(event.date);
      setLinkedForm({
        title: event.title,
        description: event.description || "",
        date: format(eventDate, "yyyy-MM-dd"),
        time: format(eventDate, "HH:mm"),
        event_type: event.event_type,
        priority: (event.priority as any) || "",
        status: event.status || "open",
        project_id: event.project_id || "",
      });
    } else {
      // Create mode - default to standalone
      setMode("standalone");
      const date = initialDate || new Date();
      const dateStr = format(date, "yyyy-MM-dd");
      const timeStr = format(date, "HH:mm");

      // Initialize standalone form
      setStandaloneForm({
        title: "",
        description: "",
        start_date: dateStr,
        start_time: timeStr,
        end_date: dateStr,
        end_time: format(new Date(date.getTime() + 60 * 60 * 1000), "HH:mm"), // +1 hour
        all_day: false,
        location: "",
        category: "other",
        color: "#3B82F6",
        reminder_minutes: "",
      });

      // Initialize linked form
      setLinkedForm({
        title: "",
        description: "",
        date: dateStr,
        time: timeStr,
        event_type: "issue",
        priority: "",
        status: "open",
        project_id: "",
      });
    }
  }, [event, initialDate, isOpen]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);

    try {
      if (mode === "standalone") {
        // Create standalone calendar event
        const startDateTime = standaloneForm.all_day
          ? new Date(standaloneForm.start_date).toISOString()
          : new Date(`${standaloneForm.start_date}T${standaloneForm.start_time}`).toISOString();

        const endDateTime = standaloneForm.all_day
          ? new Date(standaloneForm.end_date).toISOString()
          : standaloneForm.end_date && standaloneForm.end_time
          ? new Date(`${standaloneForm.end_date}T${standaloneForm.end_time}`).toISOString()
          : null;

        await calendarEventsApi.create({
          title: standaloneForm.title,
          description: standaloneForm.description || null,
          start_date: startDateTime,
          end_date: endDateTime,
          all_day: standaloneForm.all_day,
          location: standaloneForm.location || null,
          category: standaloneForm.category,
          color: standaloneForm.color || null,
          is_recurring: false,
          recurrence_rule: null,
          reminder_minutes: standaloneForm.reminder_minutes
            ? parseInt(standaloneForm.reminder_minutes)
            : null,
          is_completed: false,
          is_cancelled: false,
        });

        // Refresh calendar
        await onSave();
      } else {
        // Create linked event (existing logic)
        const dateTime = new Date(`${linkedForm.date}T${linkedForm.time}`);

        const eventData: Partial<CalendarEvent> = {
          title: linkedForm.title,
          description: linkedForm.description || null,
          date: dateTime.toISOString(),
          event_type: linkedForm.event_type,
          priority: linkedForm.priority || null,
          status: linkedForm.status,
          project_id: linkedForm.project_id || null,
        };

        if (event) {
          eventData.id = event.id;
        }

        await onSave(eventData);
      }

      onClose();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to save event");
    } finally {
      setLoading(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-background/80 backdrop-blur-sm"
        onClick={onClose}
      />

      {/* Modal */}
      <div className="relative bg-card border rounded-lg shadow-lg w-full max-w-2xl max-h-[90vh] overflow-y-auto m-4">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b">
          <h2 className="text-2xl font-bold">
            {event ? "Edit Event" : "Create Event"}
          </h2>
          <button
            onClick={onClose}
            className="p-2 hover:bg-accent rounded-lg transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="p-6 space-y-6">
          {/* Error Message */}
          {error && (
            <div className="flex items-center gap-2 p-3 bg-destructive/10 border border-destructive rounded-lg">
              <AlertCircle className="w-5 h-5 text-destructive" />
              <span className="text-sm text-destructive">{error}</span>
            </div>
          )}

          {/* Mode Toggle (only for create) */}
          {!event && (
            <div className="flex gap-2 p-1 bg-muted rounded-lg">
              <button
                type="button"
                onClick={() => setMode("standalone")}
                className={cn(
                  "flex-1 flex items-center justify-center gap-2 px-4 py-2 rounded-md transition-colors",
                  mode === "standalone"
                    ? "bg-background shadow-sm"
                    : "hover:bg-background/50"
                )}
              >
                <CalendarDays className="w-4 h-4" />
                <span>Event</span>
              </button>
              <button
                type="button"
                onClick={() => setMode("linked")}
                className={cn(
                  "flex-1 flex items-center justify-center gap-2 px-4 py-2 rounded-md transition-colors",
                  mode === "linked"
                    ? "bg-background shadow-sm"
                    : "hover:bg-background/50"
                )}
              >
                <Link2 className="w-4 h-4" />
                <span>Link to Item</span>
              </button>
            </div>
          )}

          {/* Standalone Event Form */}
          {mode === "standalone" && (
            <>
              {/* Title */}
              <div className="space-y-2">
                <label className="text-sm font-medium">Title</label>
                <input
                  type="text"
                  value={standaloneForm.title}
                  onChange={(e) =>
                    setStandaloneForm({ ...standaloneForm, title: e.target.value })
                  }
                  className="w-full px-3 py-2 bg-background border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary"
                  placeholder="Enter event title..."
                  required
                />
              </div>

              {/* Description */}
              <div className="space-y-2">
                <label className="text-sm font-medium">Description</label>
                <textarea
                  value={standaloneForm.description}
                  onChange={(e) =>
                    setStandaloneForm({ ...standaloneForm, description: e.target.value })
                  }
                  className="w-full px-3 py-2 bg-background border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary min-h-[80px] resize-y"
                  placeholder="Enter event description..."
                />
              </div>

              {/* All Day Toggle */}
              <div className="flex items-center gap-2">
                <input
                  type="checkbox"
                  id="all-day"
                  checked={standaloneForm.all_day}
                  onChange={(e) =>
                    setStandaloneForm({ ...standaloneForm, all_day: e.target.checked })
                  }
                  className="w-4 h-4 rounded border-gray-300 text-primary focus:ring-primary"
                />
                <label htmlFor="all-day" className="text-sm font-medium">
                  All day event
                </label>
              </div>

              {/* Start Date/Time */}
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <label className="text-sm font-medium flex items-center gap-2">
                    <Calendar className="w-4 h-4" />
                    Start Date
                  </label>
                  <input
                    type="date"
                    value={standaloneForm.start_date}
                    onChange={(e) =>
                      setStandaloneForm({ ...standaloneForm, start_date: e.target.value })
                    }
                    className="w-full px-3 py-2 bg-background border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary"
                    required
                  />
                </div>
                {!standaloneForm.all_day && (
                  <div className="space-y-2">
                    <label className="text-sm font-medium flex items-center gap-2">
                      <Clock className="w-4 h-4" />
                      Start Time
                    </label>
                    <input
                      type="time"
                      value={standaloneForm.start_time}
                      onChange={(e) =>
                        setStandaloneForm({ ...standaloneForm, start_time: e.target.value })
                      }
                      className="w-full px-3 py-2 bg-background border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary"
                      required
                    />
                  </div>
                )}
              </div>

              {/* End Date/Time */}
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <label className="text-sm font-medium">End Date</label>
                  <input
                    type="date"
                    value={standaloneForm.end_date}
                    onChange={(e) =>
                      setStandaloneForm({ ...standaloneForm, end_date: e.target.value })
                    }
                    className="w-full px-3 py-2 bg-background border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary"
                  />
                </div>
                {!standaloneForm.all_day && (
                  <div className="space-y-2">
                    <label className="text-sm font-medium">End Time</label>
                    <input
                      type="time"
                      value={standaloneForm.end_time}
                      onChange={(e) =>
                        setStandaloneForm({ ...standaloneForm, end_time: e.target.value })
                      }
                      className="w-full px-3 py-2 bg-background border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary"
                    />
                  </div>
                )}
              </div>

              {/* Location */}
              <div className="space-y-2">
                <label className="text-sm font-medium flex items-center gap-2">
                  <MapPin className="w-4 h-4" />
                  Location
                </label>
                <input
                  type="text"
                  value={standaloneForm.location}
                  onChange={(e) =>
                    setStandaloneForm({ ...standaloneForm, location: e.target.value })
                  }
                  className="w-full px-3 py-2 bg-background border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary"
                  placeholder="Add location..."
                />
              </div>

              {/* Category and Color */}
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <label className="text-sm font-medium">Category</label>
                  <select
                    value={standaloneForm.category}
                    onChange={(e) =>
                      setStandaloneForm({
                        ...standaloneForm,
                        category: e.target.value as StandaloneEventCategory,
                      })
                    }
                    className="w-full px-3 py-2 bg-background border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary"
                  >
                    <option value="personal">Personal</option>
                    <option value="work">Work</option>
                    <option value="meeting">Meeting</option>
                    <option value="deadline">Deadline</option>
                    <option value="appointment">Appointment</option>
                    <option value="reminder">Reminder</option>
                    <option value="holiday">Holiday</option>
                    <option value="other">Other</option>
                  </select>
                </div>
                <div className="space-y-2">
                  <label className="text-sm font-medium">Color</label>
                  <input
                    type="color"
                    value={standaloneForm.color}
                    onChange={(e) =>
                      setStandaloneForm({ ...standaloneForm, color: e.target.value })
                    }
                    className="w-full h-10 px-1 py-1 bg-background border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary"
                  />
                </div>
              </div>

              {/* Reminder */}
              <div className="space-y-2">
                <label className="text-sm font-medium">Reminder</label>
                <select
                  value={standaloneForm.reminder_minutes}
                  onChange={(e) =>
                    setStandaloneForm({ ...standaloneForm, reminder_minutes: e.target.value })
                  }
                  className="w-full px-3 py-2 bg-background border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary"
                >
                  <option value="">No reminder</option>
                  <option value="5">5 minutes before</option>
                  <option value="15">15 minutes before</option>
                  <option value="30">30 minutes before</option>
                  <option value="60">1 hour before</option>
                  <option value="1440">1 day before</option>
                </select>
              </div>
            </>
          )}

          {/* Linked Event Form */}
          {mode === "linked" && (
            <>
              {/* Event Type */}
              <div className="space-y-2">
                <label className="text-sm font-medium">Link to</label>
                <select
                  value={linkedForm.event_type}
                  onChange={(e) =>
                    setLinkedForm({ ...linkedForm, event_type: e.target.value as EventType })
                  }
                  className="w-full px-3 py-2 bg-background border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary"
                  required
                >
                  <option value="issue">Issue</option>
                  <option value="milestone">Milestone</option>
                  <option value="initiative">Initiative</option>
                  <option value="podcast_episode">Podcast Episode</option>
                  <option value="literature">Literature</option>
                </select>
              </div>

              {/* Title */}
              <div className="space-y-2">
                <label className="text-sm font-medium">Title</label>
                <input
                  type="text"
                  value={linkedForm.title}
                  onChange={(e) => setLinkedForm({ ...linkedForm, title: e.target.value })}
                  className="w-full px-3 py-2 bg-background border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary"
                  placeholder="Enter event title..."
                  required
                />
              </div>

              {/* Description */}
              <div className="space-y-2">
                <label className="text-sm font-medium">Description</label>
                <textarea
                  value={linkedForm.description}
                  onChange={(e) =>
                    setLinkedForm({ ...linkedForm, description: e.target.value })
                  }
                  className="w-full px-3 py-2 bg-background border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary min-h-[80px] resize-y"
                  placeholder="Enter event description..."
                />
              </div>

              {/* Date and Time */}
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <label className="text-sm font-medium flex items-center gap-2">
                    <Calendar className="w-4 h-4" />
                    Date
                  </label>
                  <input
                    type="date"
                    value={linkedForm.date}
                    onChange={(e) => setLinkedForm({ ...linkedForm, date: e.target.value })}
                    className="w-full px-3 py-2 bg-background border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary"
                    required
                  />
                </div>
                <div className="space-y-2">
                  <label className="text-sm font-medium flex items-center gap-2">
                    <Clock className="w-4 h-4" />
                    Time
                  </label>
                  <input
                    type="time"
                    value={linkedForm.time}
                    onChange={(e) => setLinkedForm({ ...linkedForm, time: e.target.value })}
                    className="w-full px-3 py-2 bg-background border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary"
                    required
                  />
                </div>
              </div>

              {/* Priority */}
              <div className="space-y-2">
                <label className="text-sm font-medium">Priority</label>
                <select
                  value={linkedForm.priority}
                  onChange={(e) => setLinkedForm({ ...linkedForm, priority: e.target.value as any })}
                  className="w-full px-3 py-2 bg-background border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary"
                >
                  <option value="">None</option>
                  <option value="low">Low</option>
                  <option value="medium">Medium</option>
                  <option value="high">High</option>
                  <option value="critical">Critical</option>
                </select>
              </div>

              {/* Status */}
              <div className="space-y-2">
                <label className="text-sm font-medium">Status</label>
                <select
                  value={linkedForm.status}
                  onChange={(e) => setLinkedForm({ ...linkedForm, status: e.target.value })}
                  className="w-full px-3 py-2 bg-background border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary"
                >
                  {linkedForm.event_type === "issue" && (
                    <>
                      <option value="open">Open</option>
                      <option value="in_progress">In Progress</option>
                      <option value="review">Review</option>
                      <option value="testing">Testing</option>
                      <option value="closed">Closed</option>
                    </>
                  )}
                  {linkedForm.event_type === "milestone" && (
                    <>
                      <option value="planned">Planned</option>
                      <option value="in_progress">In Progress</option>
                      <option value="completed">Completed</option>
                      <option value="cancelled">Cancelled</option>
                    </>
                  )}
                  {linkedForm.event_type === "initiative" && (
                    <>
                      <option value="planning">Planning</option>
                      <option value="in_progress">In Progress</option>
                      <option value="on_hold">On Hold</option>
                      <option value="completed">Completed</option>
                      <option value="cancelled">Cancelled</option>
                    </>
                  )}
                </select>
              </div>

              {/* Project ID */}
              <div className="space-y-2">
                <label className="text-sm font-medium">
                  Project ID <span className="text-muted-foreground">(optional)</span>
                </label>
                <input
                  type="text"
                  value={linkedForm.project_id}
                  onChange={(e) => setLinkedForm({ ...linkedForm, project_id: e.target.value })}
                  className="w-full px-3 py-2 bg-background border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary"
                  placeholder="Enter project UUID..."
                />
              </div>
            </>
          )}

          {/* Actions */}
          <div className="flex items-center justify-end gap-3 pt-4 border-t">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 hover:bg-accent rounded-lg transition-colors"
              disabled={loading}
            >
              Cancel
            </button>
            <button
              type="submit"
              className={cn(
                "px-6 py-2 bg-primary text-primary-foreground rounded-lg font-medium",
                "hover:bg-primary/90 transition-colors",
                loading && "opacity-50 cursor-not-allowed"
              )}
              disabled={loading}
            >
              {loading ? "Saving..." : event ? "Update Event" : "Create Event"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
