import { apiClient } from "./client";

export const savedFiltersApi = {
  async list(params?: any): Promise<any[]> {
    const { data } = await apiClient.get("/savedFilters/", { params });
    return data;
  },

  async get(id: string): Promise<any> {
    const { data } = await apiClient.get(`/savedFilters/${id}`);
    return data;
  },

  async create(item: any): Promise<any> {
    const { data } = await apiClient.post("/savedFilters/", item);
    return data;
  },

  async update(id: string, updates: any): Promise<any> {
    const { data } = await apiClient.put(`/savedFilters/${id}`, updates);
    return data;
  },

  async delete(id: string): Promise<void> {
    await apiClient.delete(`/savedFilters/${id}`);
  },
};

export default savedFiltersApi;
