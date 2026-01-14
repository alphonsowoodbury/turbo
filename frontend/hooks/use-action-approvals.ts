import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { actionApprovalsApi } from "@/lib/api/action-approvals";
import type {
  ActionStatus,
  ActionRiskLevel,
  ApproveActionRequest,
  DenyActionRequest,
} from "@/lib/types";

export function useActionApprovals(params?: {
  status?: ActionStatus;
  entity_type?: string;
  risk_level?: ActionRiskLevel;
  limit?: number;
  offset?: number;
}) {
  return useQuery({
    queryKey: ["action-approvals", params],
    queryFn: () => actionApprovalsApi.list(params),
  });
}

export function usePendingApprovals(params?: {
  entity_type?: string;
  risk_level?: ActionRiskLevel;
  limit?: number;
  offset?: number;
}) {
  return useQuery({
    queryKey: ["action-approvals", "pending", params],
    queryFn: () => actionApprovalsApi.getPending(params),
    refetchInterval: 5000, // Auto-refresh every 5 seconds for real-time updates
  });
}

export function useEntityApprovals(
  entity_type: string | null,
  entity_id: string | null,
  status?: ActionStatus
) {
  return useQuery({
    queryKey: ["action-approvals", "entity", entity_type, entity_id, status],
    queryFn: () => actionApprovalsApi.getByEntity(entity_type!, entity_id!, status),
    enabled: !!entity_type && !!entity_id,
  });
}

export function useActionApproval(id: string | null) {
  return useQuery({
    queryKey: ["action-approvals", id],
    queryFn: () => actionApprovalsApi.get(id!),
    enabled: !!id,
  });
}

export function useApproveAction() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, request }: { id: string; request: ApproveActionRequest }) =>
      actionApprovalsApi.approve(id, request),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["action-approvals"] });
    },
  });
}

export function useDenyAction() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, request }: { id: string; request: DenyActionRequest }) =>
      actionApprovalsApi.deny(id, request),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["action-approvals"] });
    },
  });
}

export function useDeleteActionApproval() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) => actionApprovalsApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["action-approvals"] });
    },
  });
}
