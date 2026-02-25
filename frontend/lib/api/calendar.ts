import { apiClient } from "./client";

export const calendarApi = {
  async list(params?: any): Promise<any[]> {
    const { data } = await apiClient.get("/calendar/", { params });
    return data;
  },

  async get(id: string): Promise<any> {
    const { data } = await apiClient.get(`/calendar/${id}`);
    return data;
  },

  async create(item: any): Promise<any> {
    const { data } = await apiClient.post("/calendar/", item);
    return data;
  },

  async update(id: string, updates: any): Promise<any> {
    const { data } = await apiClient.put(`/calendar/${id}`, updates);
    return data;
  },

  async delete(id: string): Promise<void> {
    await apiClient.delete(`/calendar/${id}`);
  },
};

export default calendarApi;
