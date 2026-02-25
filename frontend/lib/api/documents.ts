import { apiClient } from "./client";

export const documentsApi = {
  async list(params?: any): Promise<any[]> {
    const { data } = await apiClient.get("/documents/", { params });
    return data;
  },

  async get(id: string): Promise<any> {
    const { data } = await apiClient.get(`/documents/${id}`);
    return data;
  },

  async create(item: any): Promise<any> {
    const { data } = await apiClient.post("/documents/", item);
    return data;
  },

  async update(id: string, updates: any): Promise<any> {
    const { data } = await apiClient.put(`/documents/${id}`, updates);
    return data;
  },

  async delete(id: string): Promise<void> {
    await apiClient.delete(`/documents/${id}`);
  },
};

export default documentsApi;
