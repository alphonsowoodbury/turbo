import { apiClient } from "./client";

export const blueprintsApi = {
  async list(params?: any): Promise<any[]> {
    const { data } = await apiClient.get("/blueprints/", { params });
    return data;
  },

  async get(id: string): Promise<any> {
    const { data } = await apiClient.get(`/blueprints/${id}`);
    return data;
  },

  async create(item: any): Promise<any> {
    const { data } = await apiClient.post("/blueprints/", item);
    return data;
  },

  async update(id: string, updates: any): Promise<any> {
    const { data } = await apiClient.put(`/blueprints/${id}`, updates);
    return data;
  },

  async delete(id: string): Promise<void> {
    await apiClient.delete(`/blueprints/${id}`);
  },

  async getVersions(name: string): Promise<any[]> {
    const { data } = await apiClient.get(`/blueprints/versions/${name}`);
    return data;
  },

  async getStats(): Promise<any> {
    const { data } = await apiClient.get("/blueprints/stats");
    return data;
  },
};

export default blueprintsApi;
