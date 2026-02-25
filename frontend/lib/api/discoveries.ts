import { apiClient } from "./client";

export const discoveriesApi = {
  async list(params?: any): Promise<any[]> {
    const { data } = await apiClient.get("/discoveries/", { params });
    return data;
  },

  async get(id: string): Promise<any> {
    const { data } = await apiClient.get(`/discoveries/${id}`);
    return data;
  },

  async create(item: any): Promise<any> {
    const { data } = await apiClient.post("/discoveries/", item);
    return data;
  },

  async update(id: string, updates: any): Promise<any> {
    const { data } = await apiClient.put(`/discoveries/${id}`, updates);
    return data;
  },

  async delete(id: string): Promise<void> {
    await apiClient.delete(`/discoveries/${id}`);
  },
};

export default discoveriesApi;
