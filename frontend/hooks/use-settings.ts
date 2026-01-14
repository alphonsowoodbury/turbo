/**
 * React Hook for Settings API
 */

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8001";

export interface ClaudeStatus {
  available: boolean;
  authenticated?: boolean;
  subagents_count?: number;
  error?: string;
}

/**
 * Hook to get Claude service status
 */
export function useClaudeStatus() {
  return useQuery({
    queryKey: ["settings", "claude", "status"],
    queryFn: async () => {
      const response = await fetch(`${API_BASE}/api/v1/settings/claude/status`);

      if (!response.ok) {
        throw new Error("Failed to fetch Claude status");
      }

      return response.json() as Promise<ClaudeStatus>;
    },
    refetchInterval: 30000, // Refetch every 30 seconds
  });
}

export interface ClaudeApiKeyStatus {
  configured: boolean;
  source: "database" | "environment" | "none";
  masked_key?: string;
}

/**
 * Hook to get Claude API key status
 */
export function useClaudeApiKey() {
  return useQuery({
    queryKey: ["settings", "claude", "api-key"],
    queryFn: async () => {
      const response = await fetch(`${API_BASE}/api/v1/settings/claude/api-key`);

      if (!response.ok) {
        throw new Error("Failed to fetch API key status");
      }

      return response.json() as Promise<ClaudeApiKeyStatus>;
    },
  });
}

/**
 * Hook to update Claude API key
 */
export function useUpdateClaudeApiKey() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (apiKey: string) => {
      const response = await fetch(
        `${API_BASE}/api/v1/settings/claude/api-key`,
        {
          method: "PUT",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({ api_key: apiKey }),
        }
      );

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || "Failed to update API key");
      }

      return response.json();
    },
    onSuccess: () => {
      // Invalidate queries to refetch
      queryClient.invalidateQueries({ queryKey: ["settings", "claude"] });
    },
  });
}
