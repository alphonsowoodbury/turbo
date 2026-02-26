import { useEffect, useRef, useCallback } from "react";
import { useQueryClient } from "@tanstack/react-query";

interface UseEventStreamOptions {
  enabled?: boolean;
  eventTypes?: string[];
}

const EVENT_TO_QUERY_KEY: Record<string, string[][]> = {
  "issue": [["issues"], ["work-queue"]],
  "project": [["projects"]],
  "milestone": [["milestones"]],
  "initiative": [["initiatives"]],
  "document": [["documents"]],
  "note": [["notes"]],
  "tag": [["tags"]],
};

export function useEventStream({
  enabled = true,
  eventTypes,
}: UseEventStreamOptions = {}) {
  const queryClient = useQueryClient();
  const eventSourceRef = useRef<EventSource | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout>();
  const reconnectAttemptsRef = useRef(0);
  const lastEventIdRef = useRef<string>();
  const maxReconnectAttempts = 10;

  const connect = useCallback(() => {
    if (!enabled) return;

    if (eventSourceRef.current) {
      eventSourceRef.current.close();
    }

    const baseUrl = process.env.NEXT_PUBLIC_API_URL || "";
    let url = `${baseUrl}/api/v1/events/stream`;

    const params = new URLSearchParams();
    if (lastEventIdRef.current) {
      params.set("since", lastEventIdRef.current);
    }
    if (params.toString()) {
      url += `?${params.toString()}`;
    }

    try {
      const es = new EventSource(url);

      es.onopen = () => {
        reconnectAttemptsRef.current = 0;
      };

      es.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);

          if (event.lastEventId) {
            lastEventIdRef.current = event.lastEventId;
          }

          const eventType: string = data.event_type || data.type || "";

          // Check if this event type matches our filter
          if (eventTypes && eventTypes.length > 0) {
            const matches = eventTypes.some((filter) => {
              if (filter.endsWith(".*")) {
                return eventType.startsWith(filter.slice(0, -2));
              }
              return eventType === filter;
            });
            if (!matches) return;
          }

          // Extract entity prefix (e.g., "issue" from "issue.created")
          const entityPrefix = eventType.split(".")[0];

          const queryKeys = EVENT_TO_QUERY_KEY[entityPrefix];
          if (queryKeys) {
            queryKeys.forEach((key) => {
              queryClient.invalidateQueries({ queryKey: key });
            });
          }
        } catch {
          // Ignore unparseable messages (heartbeats, etc.)
        }
      };

      es.onerror = () => {
        es.close();
        eventSourceRef.current = null;

        if (enabled && reconnectAttemptsRef.current < maxReconnectAttempts) {
          const delay = Math.min(
            1000 * Math.pow(2, reconnectAttemptsRef.current),
            30000
          );
          reconnectTimeoutRef.current = setTimeout(() => {
            reconnectAttemptsRef.current++;
            connect();
          }, delay);
        }
      };

      eventSourceRef.current = es;
    } catch {
      // EventSource creation failed
    }
  }, [enabled, eventTypes, queryClient]);

  useEffect(() => {
    connect();

    return () => {
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
      if (eventSourceRef.current) {
        eventSourceRef.current.close();
        eventSourceRef.current = null;
      }
    };
  }, [connect]);
}
