import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";

export interface WorktreeInfo {
  path: string;
  branch: string;
  commit_hash: string;
  is_locked: boolean;
  issue_key: string | null;
}

export interface WorktreeListResponse {
  worktrees: WorktreeInfo[];
  total: number;
  worktree_base_path: string;
}

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8001/api/v1";

export function useWorktrees() {
  return useQuery<WorktreeListResponse>({
    queryKey: ["worktrees"],
    queryFn: async () => {
      const response = await fetch(`${API_URL}/worktrees/`);
      if (!response.ok) {
        throw new Error("Failed to fetch worktrees");
      }
      return response.json();
    },
    refetchInterval: 5000, // Auto-refresh every 5 seconds
  });
}

export function useDeleteWorktree() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (issueKey: string) => {
      const response = await fetch(`${API_URL}/worktrees/${issueKey}`, {
        method: "DELETE",
      });
      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || "Failed to delete worktree");
      }
      return response.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["worktrees"] });
    },
  });
}
