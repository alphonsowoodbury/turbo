import { apiClient } from "./client";

export const milestonesApi = {
  async list(params?: any): Promise<any[]> {
    const { data } = await apiClient.get("/milestones/", { params });
    return data;
  },

  async get(id: string): Promise<any> {
    const { data } = await apiClient.get(`/milestones/${id}`);
    return data;
  },

  async create(item: any): Promise<any> {
    const { data } = await apiClient.post("/milestones/", item);
    return data;
  },

  async update(id: string, updates: any): Promise<any> {
    const { data } = await apiClient.put(`/milestones/${id}`, updates);
    return data;
  },

  async delete(id: string): Promise<void> {
    await apiClient.delete(`/milestones/${id}`);
  },
};

export default milestonesApi;
