import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { favoritesApi, type FavoriteCreate } from "@/lib/api/favorites";

export function useFavorites() {
  return useQuery({
    queryKey: ["favorites"],
    queryFn: () => favoritesApi.list(),
  });
}

export function useIsFavorite(itemType: string, itemId: string) {
  const { data: favorites = [] } = useFavorites();
  return favorites.some(
    (f) => f.item_type === itemType && f.item_id === itemId
  );
}

export function useFavoriteId(itemType: string, itemId: string) {
  const { data: favorites = [] } = useFavorites();
  return favorites.find(
    (f) => f.item_type === itemType && f.item_id === itemId
  )?.id;
}

export function useCreateFavorite() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: FavoriteCreate) => favoritesApi.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["favorites"] });
    },
  });
}

export function useDeleteFavorite() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) => favoritesApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["favorites"] });
    },
  });
}

export function useDeleteFavoriteByItem() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ itemType, itemId }: { itemType: string; itemId: string }) =>
      favoritesApi.deleteByItem(itemType, itemId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["favorites"] });
    },
  });
}

export function useToggleFavorite() {
  const createFavorite = useCreateFavorite();
  const deleteFavorite = useDeleteFavoriteByItem();

  return {
    toggle: (itemType: string, itemId: string, isFavorited: boolean) => {
      if (isFavorited) {
        deleteFavorite.mutate({ itemType, itemId });
      } else {
        createFavorite.mutate({ item_type: itemType, item_id: itemId });
      }
    },
    isPending: createFavorite.isPending || deleteFavorite.isPending,
  };
}