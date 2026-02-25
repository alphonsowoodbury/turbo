import { apiClient } from "./client";

export const agentsApi = {
  async list(params?: any): Promise<any[]> {
    const { data } = await apiClient.get("/agents/", { params });
    return data;
  },

  async get(id: string): Promise<any> {
    const { data } = await apiClient.get(`/agents/${id}`);
    return data;
  },

  async create(item: any): Promise<any> {
    const { data } = await apiClient.post("/agents/", item);
    return data;
  },

  async update(id: string, updates: any): Promise<any> {
    const { data } = await apiClient.put(`/agents/${id}`, updates);
    return data;
  },

  async delete(id: string): Promise<void> {
    await apiClient.delete(`/agents/${id}`);
  },

  async getActive(): Promise<any> {
    const { data } = await apiClient.get("/agents/active");
    return data;
  },

  async getRecent(limit: number = 50): Promise<any> {
    const { data } = await apiClient.get("/agents/recent", { params: { limit } });
    return data;
  },

  async getStats(): Promise<any> {
    const { data } = await apiClient.get("/agents/stats");
    return data;
  },

  async getSession(sessionId: string): Promise<any> {
    const { data } = await apiClient.get(`/agents/sessions/${sessionId}`);
    return data;
  },

  async getConfigured(): Promise<any[]> {
    const { data } = await apiClient.get("/agents/configured");
    return data;
  },

  async getConfiguredAgent(agentName: string): Promise<any> {
    const { data } = await apiClient.get(`/agents/configured/${agentName}`);
    return data;
  },

  async getAgentSessions(agentName: string, limit: number = 50): Promise<any> {
    const { data } = await apiClient.get(`/agents/configured/${agentName}/sessions`, { params: { limit } });
    return data;
  },
};

export default agentsApi;
