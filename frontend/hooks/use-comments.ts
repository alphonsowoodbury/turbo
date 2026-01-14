import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { commentsApi } from "@/lib/api/comments";
import type { CommentCreate, CommentUpdate, EntityType } from "@/lib/types";

export function useComments(entityType: EntityType | null, entityId: string | null) {
  return useQuery({
    queryKey: ["comments", entityType, entityId],
    queryFn: () => commentsApi.listByEntity(entityType!, entityId!),
    enabled: !!entityType && !!entityId,
    refetchOnWindowFocus: true, // Refetch when returning to tab
  });
}

export function useComment(id: string | null) {
  return useQuery({
    queryKey: ["comments", id],
    queryFn: () => commentsApi.get(id!),
    enabled: !!id,
  });
}

export function useCreateComment() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (comment: CommentCreate) => commentsApi.create(comment),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ["comments", data.entity_type, data.entity_id] });
    },
  });
}

export function useUpdateComment() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: CommentUpdate }) =>
      commentsApi.update(id, data),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ["comments", data.entity_type, data.entity_id] });
      queryClient.invalidateQueries({ queryKey: ["comments", data.id] });
    },
  });
}

export function useDeleteComment() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, entityType, entityId }: { id: string; entityType: EntityType; entityId: string }) =>
      commentsApi.delete(id),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ["comments", variables.entityType, variables.entityId] });
    },
  });
}
