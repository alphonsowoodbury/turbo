import { apiClient } from "./client";

export const formsApi = {
  async list(params?: any): Promise<any[]> {
    const { data } = await apiClient.get("/forms/", { params });
    return data;
  },

  async get(id: string): Promise<any> {
    const { data } = await apiClient.get(`/forms/${id}`);
    return data;
  },

  async create(item: any): Promise<any> {
    const { data } = await apiClient.post("/forms/", item);
    return data;
  },

  async update(id: string, updates: any): Promise<any> {
    const { data } = await apiClient.put(`/forms/${id}`, updates);
    return data;
  },

  async delete(id: string): Promise<void> {
    await apiClient.delete(`/forms/${id}`);
  },
};

export default formsApi;
