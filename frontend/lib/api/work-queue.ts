import { apiClient } from "./client";

export const workQueueApi = {
  async list(params?: any): Promise<any[]> {
    const { data } = await apiClient.get("/workQueue/", { params });
    return data;
  },

  async get(id: string): Promise<any> {
    const { data } = await apiClient.get(`/workQueue/${id}`);
    return data;
  },

  async create(item: any): Promise<any> {
    const { data } = await apiClient.post("/workQueue/", item);
    return data;
  },

  async update(id: string, updates: any): Promise<any> {
    const { data } = await apiClient.put(`/workQueue/${id}`, updates);
    return data;
  },

  async delete(id: string): Promise<void> {
    await apiClient.delete(`/workQueue/${id}`);
  },
};

export default workQueueApi;
