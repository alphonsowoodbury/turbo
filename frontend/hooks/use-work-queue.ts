import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";

const API_BASE = "http://localhost:8001/api/v1";

interface Issue {
  id: string;
  title: string;
  description: string;
  type: string;
  status: string;
  priority: string;
  work_rank: number | null;
  last_ranked_at: string | null;
  project_id: string | null;
  created_at: string;
  updated_at: string;
}

interface WorkQueueParams {
  status?: string;
  priority?: string;
  limit?: number;
  includeUnranked?: boolean;
}

export function useWorkQueue(params?: WorkQueueParams) {
  return useQuery<Issue[]>({
    queryKey: ["work-queue", params],
    queryFn: async () => {
      const searchParams = new URLSearchParams();
      if (params?.status) searchParams.append("status", params.status);
      if (params?.priority) searchParams.append("priority", params.priority);
      if (params?.limit) searchParams.append("limit", params.limit.toString());
      if (params?.includeUnranked) searchParams.append("include_unranked", "true");

      const response = await fetch(`${API_BASE}/work-queue/?${searchParams}`);
      if (!response.ok) throw new Error("Failed to fetch work queue");
      return response.json();
    },
  });
}

export function useNextIssue() {
  return useQuery<Issue | null>({
    queryKey: ["work-queue", "next"],
    queryFn: async () => {
      const response = await fetch(`${API_BASE}/work-queue/next`);
      if (!response.ok) throw new Error("Failed to fetch next issue");
      const data = await response.json();
      return data || null;
    },
  });
}

export function useSetIssueRank() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ issueId, rank }: { issueId: string; rank: number }) => {
      const response = await fetch(`${API_BASE}/work-queue/${issueId}/rank`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ work_rank: rank }),
      });
      if (!response.ok) throw new Error("Failed to set issue rank");
      return response.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["work-queue"] });
      queryClient.invalidateQueries({ queryKey: ["issues"] });
    },
  });
}

export function useRemoveIssueRank() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (issueId: string) => {
      const response = await fetch(`${API_BASE}/work-queue/${issueId}/rank`, {
        method: "DELETE",
      });
      if (!response.ok) throw new Error("Failed to remove issue rank");
      return response.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["work-queue"] });
      queryClient.invalidateQueries({ queryKey: ["issues"] });
      toast.success("Issue removed from work queue");
    },
    onError: () => {
      toast.error("Failed to remove issue from queue");
    },
  });
}

export function useBulkRerank() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (issueRanks: Array<{ issue_id: string; rank: number }>) => {
      const response = await fetch(`${API_BASE}/work-queue/bulk-rerank`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ issue_ranks: issueRanks }),
      });
      if (!response.ok) throw new Error("Failed to bulk rerank issues");
      return response.json();
    },
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ["work-queue"] });
      queryClient.invalidateQueries({ queryKey: ["issues"] });
      toast.success(`Updated ${data.updated_count} issue ranks`);
    },
    onError: () => {
      toast.error("Failed to update issue ranks");
    },
  });
}

export function useAutoRankIssues() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async () => {
      const response = await fetch(`${API_BASE}/work-queue/auto-rank`, {
        method: "POST",
      });
      if (!response.ok) throw new Error("Failed to auto-rank issues");
      return response.json();
    },
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ["work-queue"] });
      queryClient.invalidateQueries({ queryKey: ["issues"] });
      toast.success(`Auto-ranked ${data.ranked_count} issues`);
    },
    onError: () => {
      toast.error("Failed to auto-rank issues");
    },
  });
}
