import { useEffect, useState, useCallback } from "react";
import { useQueryClient } from "@tanstack/react-query";

interface AgentSession {
  session_id: string;
  entity_type: string;
  entity_id: string;
  status: "idle" | "starting" | "processing" | "typing" | "completed" | "error";
  started_at: string;
  updated_at: string;
  completed_at?: string;
  error?: string;
  input_tokens: number;
  output_tokens: number;
  cost_usd: number;
  duration_seconds: number;
  entity_title?: string;
  comment_count: number;
}

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8001";
const WS_URL = API_URL.replace("http", "ws");

export function useAgentActivity() {
  const [connected, setConnected] = useState(false);
  const [ws, setWs] = useState<WebSocket | null>(null);
  const queryClient = useQueryClient();

  useEffect(() => {
    const websocket = new WebSocket(`${WS_URL}/api/v1/ws/agents/activity`);

    websocket.onopen = () => {
      console.log("Connected to agent activity stream");
      setConnected(true);
    };

    websocket.onmessage = (event) => {
      const message = JSON.parse(event.data);

      switch (message.type) {
        case "initial_state":
          // Update React Query cache with initial data
          queryClient.setQueryData(["agents", "active"], {
            active_sessions: message.data.active_sessions || [],
            count: message.data.active_sessions?.length || 0,
          });
          queryClient.setQueryData(["agents", "recent", 50], {
            recent_sessions: message.data.recent_sessions || [],
            count: message.data.recent_sessions?.length || 0,
          });
          queryClient.setQueryData(["agents", "stats"], message.data.stats || {});
          break;

        case "agent_started":
        case "agent_status_update":
        case "agent_completed":
        case "agent_failed":
          // Invalidate queries to trigger refetch
          queryClient.invalidateQueries({ queryKey: ["agents", "active"] });
          queryClient.invalidateQueries({ queryKey: ["agents", "recent"] });
          queryClient.invalidateQueries({ queryKey: ["agents", "stats"] });
          break;

        case "refresh":
          queryClient.setQueryData(["agents", "active"], {
            active_sessions: message.data.active_sessions || [],
            count: message.data.active_sessions?.length || 0,
          });
          queryClient.setQueryData(["agents", "stats"], message.data.stats || {});
          break;
      }
    };

    websocket.onclose = () => {
      console.log("Disconnected from agent activity stream");
      setConnected(false);
    };

    websocket.onerror = (error) => {
      console.error("WebSocket error:", error);
    };

    setWs(websocket);

    // Cleanup
    return () => {
      websocket.close();
    };
  }, [queryClient]);

  // Ping keepalive
  useEffect(() => {
    if (!ws) return;

    const interval = setInterval(() => {
      if (ws.readyState === WebSocket.OPEN) {
        ws.send("ping");
      }
    }, 30000);

    return () => clearInterval(interval);
  }, [ws]);

  const refresh = useCallback(() => {
    if (ws && ws.readyState === WebSocket.OPEN) {
      ws.send("refresh");
    }
  }, [ws]);

  return { connected, refresh };
}
