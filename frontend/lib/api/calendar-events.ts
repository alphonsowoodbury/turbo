import { apiClient } from "./client";

export const calendarEventsApi = {
  async list(params?: any): Promise<any[]> {
    const { data } = await apiClient.get("/calendar-events/", { params });
    return data;
  },

  async get(id: string): Promise<any> {
    const { data } = await apiClient.get(`/calendar-events/${id}`);
    return data;
  },

  async create(event: any): Promise<any> {
    const { data } = await apiClient.post("/calendar-events/", event);
    return data;
  },

  async update(id: string, updates: any): Promise<any> {
    const { data} = await apiClient.put(`/calendar-events/${id}`, updates);
    return data;
  },

  async delete(id: string): Promise<void> {
    await apiClient.delete(`/calendar-events/${id}`);
  },
};

export default calendarEventsApi;
