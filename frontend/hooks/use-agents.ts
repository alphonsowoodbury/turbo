import { useQuery } from "@tanstack/react-query";
import { agentsApi } from "@/lib/api/agents";

export function useActiveAgents() {
  return useQuery({
    queryKey: ["agents", "active"],
    queryFn: () => agentsApi.getActive(),
    refetchInterval: 3000, // Poll every 3 seconds
  });
}

export function useRecentAgents(limit: number = 50) {
  return useQuery({
    queryKey: ["agents", "recent", limit],
    queryFn: () => agentsApi.getRecent(limit),
    refetchInterval: 5000, // Poll every 5 seconds
  });
}

export function useAgentStats() {
  return useQuery({
    queryKey: ["agents", "stats"],
    queryFn: () => agentsApi.getStats(),
    refetchInterval: 5000, // Poll every 5 seconds
  });
}

export function useAgentSession(sessionId: string | null) {
  return useQuery({
    queryKey: ["agents", "session", sessionId],
    queryFn: () => agentsApi.getSession(sessionId!),
    enabled: !!sessionId,
  });
}

export function useConfiguredAgents() {
  return useQuery({
    queryKey: ["agents", "configured"],
    queryFn: () => agentsApi.getConfigured(),
  });
}

export function useConfiguredAgent(agentName: string | null) {
  return useQuery({
    queryKey: ["agents", "configured", agentName],
    queryFn: () => agentsApi.getConfiguredAgent(agentName!),
    enabled: !!agentName,
  });
}

export function useAgentSessions(agentName: string | null, limit: number = 50) {
  return useQuery({
    queryKey: ["agents", "configured", agentName, "sessions", limit],
    queryFn: () => agentsApi.getAgentSessions(agentName!, limit),
    enabled: !!agentName,
  });
}
