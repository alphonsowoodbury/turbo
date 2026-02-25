import { apiClient } from "./client";

export interface FavoriteCreate {
  entity_type: string;
  entity_id: string;
}

export const favoritesApi = {
  async list(params?: any): Promise<any[]> {
    const { data } = await apiClient.get("/favorites/", { params });
    return data;
  },

  async create(favorite: FavoriteCreate): Promise<any> {
    const { data } = await apiClient.post("/favorites/", favorite);
    return data;
  },

  async delete(id: string): Promise<void> {
    await apiClient.delete(`/favorites/${id}`);
  },
};

export default favoritesApi;
