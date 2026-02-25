import { apiClient } from "./client";

export const actionApprovalsApi = {
  async list(params?: any): Promise<any[]> {
    const { data } = await apiClient.get("/actionApprovals/", { params });
    return data;
  },

  async get(id: string): Promise<any> {
    const { data } = await apiClient.get(`/actionApprovals/${id}`);
    return data;
  },

  async create(item: any): Promise<any> {
    const { data } = await apiClient.post("/actionApprovals/", item);
    return data;
  },

  async update(id: string, updates: any): Promise<any> {
    const { data } = await apiClient.put(`/actionApprovals/${id}`, updates);
    return data;
  },

  async delete(id: string): Promise<void> {
    await apiClient.delete(`/actionApprovals/${id}`);
  },

  async getPending(params?: any): Promise<any> {
    const { data } = await apiClient.get("/actionApprovals/pending", { params });
    return data;
  },

  async getByEntity(entityType: string, entityId: string, status?: string): Promise<any[]> {
    const { data } = await apiClient.get(`/actionApprovals/entity/${entityType}/${entityId}`, {
      params: status ? { status } : undefined,
    });
    return data;
  },

  async approve(id: string, request: any): Promise<any> {
    const { data } = await apiClient.post(`/actionApprovals/${id}/approve`, request);
    return data;
  },

  async deny(id: string, request: any): Promise<any> {
    const { data } = await apiClient.post(`/actionApprovals/${id}/deny`, request);
    return data;
  },
};

export default actionApprovalsApi;
