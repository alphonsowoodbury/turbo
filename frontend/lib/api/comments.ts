import { apiClient } from "./client";

export const commentsApi = {
  async list(params?: any): Promise<any[]> {
    const { data } = await apiClient.get("/comments/", { params });
    return data;
  },

  async listByEntity(entityType: string, entityId: string): Promise<any[]> {
    const { data } = await apiClient.get(`/comments/entity/${entityType}/${entityId}`);
    return data;
  },

  async get(id: string): Promise<any> {
    const { data } = await apiClient.get(`/comments/${id}`);
    return data;
  },

  async create(item: any): Promise<any> {
    const { data } = await apiClient.post("/comments/", item);
    return data;
  },

  async update(id: string, updates: any): Promise<any> {
    const { data } = await apiClient.put(`/comments/${id}`, updates);
    return data;
  },

  async delete(id: string): Promise<void> {
    await apiClient.delete(`/comments/${id}`);
  },
};

export default commentsApi;
