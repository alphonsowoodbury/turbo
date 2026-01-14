import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { savedFiltersApi, SavedFilter, SavedFilterCreate } from "@/lib/api/saved-filters";
import { toast } from "sonner";

export function useSavedFilters(projectId: string) {
  return useQuery({
    queryKey: ["saved-filters", projectId],
    queryFn: () => savedFiltersApi.listByProject(projectId),
    enabled: !!projectId,
  });
}

export function useCreateSavedFilter() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: SavedFilterCreate) => savedFiltersApi.create(data),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ["saved-filters", data.project_id] });
      toast.success("Filter saved successfully");
    },
    onError: () => {
      toast.error("Failed to save filter");
    },
  });
}

export function useDeleteSavedFilter() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) => savedFiltersApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["saved-filters"] });
      toast.success("Filter deleted successfully");
    },
    onError: () => {
      toast.error("Failed to delete filter");
    },
  });
}