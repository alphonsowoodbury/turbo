import { apiClient } from "./client";

export const issuesApi = {
  async list(params?: any): Promise<any[]> {
    const { data } = await apiClient.get("/issues/", { params });
    return data;
  },

  async get(id: string): Promise<any> {
    const { data } = await apiClient.get(`/issues/${id}`);
    return data;
  },

  async create(item: any): Promise<any> {
    const { data } = await apiClient.post("/issues/", item);
    return data;
  },

  async update(id: string, updates: any): Promise<any> {
    const { data } = await apiClient.put(`/issues/${id}`, updates);
    return data;
  },

  async delete(id: string): Promise<void> {
    await apiClient.delete(`/issues/${id}`);
  },
};

export default issuesApi;
