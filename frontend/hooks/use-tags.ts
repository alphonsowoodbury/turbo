import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { tagsApi } from "@/lib/api/tags";
import type { TagCreate, TagUpdate } from "@/lib/types";

export function useTags(params?: Record<string, unknown>) {
  return useQuery({
    queryKey: ["tags", params],
    queryFn: () => tagsApi.list(params),
  });
}

export function useTag(id: string | null) {
  return useQuery({
    queryKey: ["tags", id],
    queryFn: () => tagsApi.get(id!),
    enabled: !!id,
  });
}

export function useCreateTag() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (tag: TagCreate) => tagsApi.create(tag),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["tags"] });
    },
  });
}

export function useUpdateTag() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: TagUpdate }) =>
      tagsApi.update(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["tags"] });
    },
  });
}

export function useDeleteTag() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) => tagsApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["tags"] });
    },
  });
}
