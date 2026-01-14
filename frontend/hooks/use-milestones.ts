import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { milestonesApi } from "@/lib/api/milestones";
import type { MilestoneCreate, MilestoneUpdate } from "@/lib/types";

export function useMilestones(params?: {
  skip?: number;
  limit?: number;
  project_id?: string;
  status?: string;
  workspace?: string;
  work_company?: string;
}) {
  return useQuery({
    queryKey: ["milestones", params],
    queryFn: () => milestonesApi.list(params),
  });
}

export function useMilestone(id: string | null) {
  return useQuery({
    queryKey: ["milestones", id],
    queryFn: () => milestonesApi.get(id!),
    enabled: !!id,
  });
}

export function useMilestoneIssues(milestoneId: string | null) {
  return useQuery({
    queryKey: ["milestones", milestoneId, "issues"],
    queryFn: () => milestonesApi.getIssues(milestoneId!),
    enabled: !!milestoneId,
  });
}

export function useCreateMilestone() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (milestone: MilestoneCreate) => milestonesApi.create(milestone),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["milestones"] });
      queryClient.invalidateQueries({ queryKey: ["projects"] });
    },
  });
}

export function useUpdateMilestone() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: MilestoneUpdate }) =>
      milestonesApi.update(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["milestones"] });
      queryClient.invalidateQueries({ queryKey: ["projects"] });
    },
  });
}

export function useDeleteMilestone() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) => milestonesApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["milestones"] });
      queryClient.invalidateQueries({ queryKey: ["projects"] });
    },
  });
}