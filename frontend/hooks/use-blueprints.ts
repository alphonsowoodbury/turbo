import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { blueprintsApi } from "@/lib/api/blueprints";
import type {
  Blueprint,
  BlueprintCreate,
  BlueprintSummary,
  BlueprintUpdate,
  BlueprintCategory,
} from "@/lib/types";

// Get all blueprints with optional filters
export function useBlueprints(params?: {
  category?: BlueprintCategory;
  is_active?: boolean;
}) {
  return useQuery<BlueprintSummary[]>({
    queryKey: ["blueprints", params],
    queryFn: () => blueprintsApi.list(params),
  });
}

// Get a single blueprint by ID
export function useBlueprint(id: string | null) {
  return useQuery<Blueprint>({
    queryKey: ["blueprints", id],
    queryFn: () => blueprintsApi.get(id!),
    enabled: !!id,
  });
}

// Create a new blueprint
export function useCreateBlueprint() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (blueprint: BlueprintCreate) => blueprintsApi.create(blueprint),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["blueprints"] });
    },
  });
}

// Update a blueprint
export function useUpdateBlueprint() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: BlueprintUpdate }) =>
      blueprintsApi.update(id, data),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ["blueprints"] });
      queryClient.invalidateQueries({ queryKey: ["blueprints", data.id] });
    },
  });
}

// Delete a blueprint
export function useDeleteBlueprint() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) => blueprintsApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["blueprints"] });
    },
  });
}
