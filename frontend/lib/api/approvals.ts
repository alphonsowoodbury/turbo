import { apiClient } from "./client";

export const approvalsApi = {
  async list(params?: any): Promise<any[]> {
    const { data } = await apiClient.get("/approvals/", { params });
    return data;
  },

  async get(id: string): Promise<any> {
    const { data } = await apiClient.get(`/approvals/${id}`);
    return data;
  },

  async create(item: any): Promise<any> {
    const { data } = await apiClient.post("/approvals/", item);
    return data;
  },

  async update(id: string, updates: any): Promise<any> {
    const { data } = await apiClient.put(`/approvals/${id}`, updates);
    return data;
  },

  async delete(id: string): Promise<void> {
    await apiClient.delete(`/approvals/${id}`);
  },
};

export default approvalsApi;
