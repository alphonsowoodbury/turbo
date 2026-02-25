import { apiClient } from "./client";

export const initiativesApi = {
  async list(params?: any): Promise<any[]> {
    const { data } = await apiClient.get("/initiatives/", { params });
    return data;
  },

  async get(id: string): Promise<any> {
    const { data } = await apiClient.get(`/initiatives/${id}`);
    return data;
  },

  async create(item: any): Promise<any> {
    const { data } = await apiClient.post("/initiatives/", item);
    return data;
  },

  async update(id: string, updates: any): Promise<any> {
    const { data } = await apiClient.put(`/initiatives/${id}`, updates);
    return data;
  },

  async delete(id: string): Promise<void> {
    await apiClient.delete(`/initiatives/${id}`);
  },
};

export default initiativesApi;
