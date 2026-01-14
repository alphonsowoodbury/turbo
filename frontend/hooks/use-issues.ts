import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { issuesApi } from "@/lib/api/issues";
import type { IssueCreate, IssueUpdate } from "@/lib/types";

export function useIssues(params?: {
  skip?: number;
  limit?: number;
  project_id?: string;
  status?: string;
  priority?: string;
  type?: string;
  workspace?: string;
  work_company?: string;
}) {
  return useQuery({
    queryKey: ["issues", params],
    queryFn: () => issuesApi.list(params),
  });
}

export function useIssue(id: string | null) {
  return useQuery({
    queryKey: ["issues", id],
    queryFn: () => issuesApi.get(id!),
    enabled: !!id,
  });
}

export function useCreateIssue() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (issue: IssueCreate) => issuesApi.create(issue),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["issues"] });
      queryClient.invalidateQueries({ queryKey: ["projects"] });
    },
  });
}

export function useUpdateIssue() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: IssueUpdate }) =>
      issuesApi.update(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["issues"] });
      queryClient.invalidateQueries({ queryKey: ["projects"] });
    },
  });
}

export function useDeleteIssue() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) => issuesApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["issues"] });
      queryClient.invalidateQueries({ queryKey: ["projects"] });
    },
  });
}

export function useCloseIssue() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) => issuesApi.close(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["issues"] });
      queryClient.invalidateQueries({ queryKey: ["projects"] });
    },
  });
}

export function useAssignIssue() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, assignee }: { id: string; assignee: string }) =>
      issuesApi.assign(id, assignee),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["issues"] });
    },
  });
}