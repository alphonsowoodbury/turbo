import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import axios from "axios";

const API_BASE = "http://localhost:8001/api/v1";

interface IssueDependencies {
  blocking: string[];
  blocked_by: string[];
}

interface DependencyChain {
  issue_id: string;
  chain: string[];
}

interface CreateDependencyData {
  blocking_issue_id: string;
  blocked_issue_id: string;
  dependency_type?: string;
}

// Get all dependencies for an issue
export function useIssueDependencies(issueId: string | undefined) {
  return useQuery<IssueDependencies>({
    queryKey: ["dependencies", issueId],
    queryFn: async () => {
      if (!issueId) throw new Error("Issue ID is required");
      const response = await axios.get(`${API_BASE}/dependencies/${issueId}`);
      return response.data;
    },
    enabled: !!issueId,
  });
}

// Get dependency chain for an issue
export function useDependencyChain(issueId: string | undefined) {
  return useQuery<DependencyChain>({
    queryKey: ["dependencies", "chain", issueId],
    queryFn: async () => {
      if (!issueId) throw new Error("Issue ID is required");
      const response = await axios.get(`${API_BASE}/dependencies/${issueId}/chain`);
      return response.data;
    },
    enabled: !!issueId,
  });
}

// Create a new dependency
export function useCreateDependency() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (data: CreateDependencyData) => {
      const response = await axios.post(`${API_BASE}/dependencies/`, data);
      return response.data;
    },
    onSuccess: (data, variables) => {
      // Invalidate dependencies for both issues
      queryClient.invalidateQueries({ queryKey: ["dependencies", variables.blocking_issue_id] });
      queryClient.invalidateQueries({ queryKey: ["dependencies", variables.blocked_issue_id] });
      queryClient.invalidateQueries({ queryKey: ["dependencies", "chain", variables.blocking_issue_id] });
      queryClient.invalidateQueries({ queryKey: ["dependencies", "chain", variables.blocked_issue_id] });
    },
  });
}

// Delete a dependency
export function useDeleteDependency() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ blockingIssueId, blockedIssueId }: { blockingIssueId: string; blockedIssueId: string }) => {
      await axios.delete(`${API_BASE}/dependencies/${blockingIssueId}/${blockedIssueId}`);
    },
    onSuccess: (data, variables) => {
      // Invalidate dependencies for both issues
      queryClient.invalidateQueries({ queryKey: ["dependencies", variables.blockingIssueId] });
      queryClient.invalidateQueries({ queryKey: ["dependencies", variables.blockedIssueId] });
      queryClient.invalidateQueries({ queryKey: ["dependencies", "chain", variables.blockingIssueId] });
      queryClient.invalidateQueries({ queryKey: ["dependencies", "chain", variables.blockedIssueId] });
    },
  });
}
