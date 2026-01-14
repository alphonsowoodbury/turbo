import { useEffect, useRef, useCallback, useState } from "react";
import { useQueryClient } from "@tanstack/react-query";
import type { EntityType } from "@/lib/types";

interface WebSocketMessage {
  type: "comment_created" | "comment_updated" | "comment_deleted" | "ai_typing_start" | "ai_typing_stop";
  data: any;
}

interface UseWebSocketOptions {
  entityType: EntityType;
  entityId: string;
  enabled?: boolean;
  onMessage?: (message: WebSocketMessage) => void;
}

export function useWebSocket({
  entityType,
  entityId,
  enabled = true,
  onMessage
}: UseWebSocketOptions) {
  const queryClient = useQueryClient();
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout>();
  const reconnectAttemptsRef = useRef(0);
  const maxReconnectAttempts = 5;
  const [isTyping, setIsTyping] = useState(false);
  const [typingAuthor, setTypingAuthor] = useState<string>("");

  const connect = useCallback(() => {
    if (!enabled || !entityType || !entityId) {
      return;
    }

    // Clean up existing connection
    if (wsRef.current) {
      wsRef.current.close();
    }

    // Determine WebSocket URL based on environment
    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    const host = process.env.NEXT_PUBLIC_API_URL?.replace(/^https?:\/\//, "") || window.location.host.replace(":3001", ":8001");
    const wsUrl = `${protocol}//${host}/api/v1/ws/comments/${entityType}/${entityId}`;

    try {
      const ws = new WebSocket(wsUrl);

      ws.onopen = () => {
        console.log(`WebSocket connected to ${entityType}:${entityId}`);
        reconnectAttemptsRef.current = 0;

        // Start keepalive ping every 30 seconds
        const pingInterval = setInterval(() => {
          if (ws.readyState === WebSocket.OPEN) {
            ws.send("ping");
          }
        }, 30000);

        // Store interval ID to clear later
        (ws as any).pingInterval = pingInterval;
      };

      ws.onmessage = (event) => {
        try {
          // Handle pong responses
          if (event.data === "pong") {
            return;
          }

          const message: WebSocketMessage = JSON.parse(event.data);

          // Call custom message handler if provided
          if (onMessage) {
            onMessage(message);
          }

          // Handle different message types
          switch (message.type) {
            case "comment_created":
            case "comment_updated":
            case "comment_deleted":
              // Invalidate React Query cache to trigger refetch
              queryClient.invalidateQueries({
                queryKey: ["comments", entityType, entityId]
              });
              break;

            case "ai_typing_start":
              setIsTyping(true);
              setTypingAuthor(message.data.author_name || "Claude");
              break;

            case "ai_typing_stop":
              setIsTyping(false);
              setTypingAuthor("");
              break;
          }
        } catch (error) {
          console.error("Error parsing WebSocket message:", error);
        }
      };

      ws.onerror = (error) => {
        console.error("WebSocket error:", error);
      };

      ws.onclose = () => {
        console.log(`WebSocket disconnected from ${entityType}:${entityId}`);

        // Clear keepalive interval
        if ((ws as any).pingInterval) {
          clearInterval((ws as any).pingInterval);
        }

        // Attempt to reconnect with exponential backoff
        if (enabled && reconnectAttemptsRef.current < maxReconnectAttempts) {
          const delay = Math.min(1000 * Math.pow(2, reconnectAttemptsRef.current), 30000);
          console.log(`Reconnecting in ${delay}ms (attempt ${reconnectAttemptsRef.current + 1}/${maxReconnectAttempts})...`);

          reconnectTimeoutRef.current = setTimeout(() => {
            reconnectAttemptsRef.current++;
            connect();
          }, delay);
        }
      };

      wsRef.current = ws;
    } catch (error) {
      console.error("Error creating WebSocket:", error);
    }
  }, [entityType, entityId, enabled, queryClient, onMessage]);

  useEffect(() => {
    connect();

    // Cleanup on unmount or when dependencies change
    return () => {
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }

      if (wsRef.current) {
        // Clear keepalive interval
        if ((wsRef.current as any).pingInterval) {
          clearInterval((wsRef.current as any).pingInterval);
        }
        wsRef.current.close();
        wsRef.current = null;
      }
    };
  }, [connect]);

  return {
    isConnected: wsRef.current?.readyState === WebSocket.OPEN,
    isTyping,
    typingAuthor,
    reconnect: connect,
  };
}
