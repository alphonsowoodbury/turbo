import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { initiativesApi } from "@/lib/api/initiatives";
import type { InitiativeCreate, InitiativeUpdate } from "@/lib/types";

export function useInitiatives(params?: {
  skip?: number;
  limit?: number;
  project_id?: string;
  status?: string;
  workspace?: string;
  work_company?: string;
}) {
  return useQuery({
    queryKey: ["initiatives", params],
    queryFn: () => initiativesApi.list(params),
  });
}

export function useInitiative(id: string | null) {
  return useQuery({
    queryKey: ["initiatives", id],
    queryFn: () => initiativesApi.get(id!),
    enabled: !!id,
  });
}

export function useInitiativeIssues(initiativeId: string | null) {
  return useQuery({
    queryKey: ["initiatives", initiativeId, "issues"],
    queryFn: () => initiativesApi.getIssues(initiativeId!),
    enabled: !!initiativeId,
  });
}

export function useCreateInitiative() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (initiative: InitiativeCreate) => initiativesApi.create(initiative),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["initiatives"] });
      queryClient.invalidateQueries({ queryKey: ["projects"] });
    },
  });
}

export function useUpdateInitiative() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: InitiativeUpdate }) =>
      initiativesApi.update(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["initiatives"] });
      queryClient.invalidateQueries({ queryKey: ["projects"] });
    },
  });
}

export function useDeleteInitiative() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) => initiativesApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["initiatives"] });
      queryClient.invalidateQueries({ queryKey: ["projects"] });
    },
  });
}
