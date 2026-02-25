import { apiClient } from "./client";

export interface ScriptRun {
  id: string;
  script_name: string;
  script_path: string;
  status: string;
  command?: string;
  arguments?: string;
  triggered_by?: string;
  exit_code?: number;
  output?: string;
  error?: string;
  duration_seconds: number;
  files_processed: number;
  records_affected: number;
  started_at: string;
  completed_at?: string;
  updated_at: string;
  created_at: string;
}

export const scriptsApi = {
  async list(params?: any): Promise<any[]> {
    const { data } = await apiClient.get("/scripts/", { params });
    return data;
  },

  async get(id: string): Promise<any> {
    const { data } = await apiClient.get(`/scripts/${id}`);
    return data;
  },

  async create(item: any): Promise<any> {
    const { data } = await apiClient.post("/scripts/", item);
    return data;
  },

  async update(id: string, updates: any): Promise<any> {
    const { data } = await apiClient.put(`/scripts/${id}`, updates);
    return data;
  },

  async delete(id: string): Promise<void> {
    await apiClient.delete(`/scripts/${id}`);
  },

  async getRunning(): Promise<ScriptRun[]> {
    const { data } = await apiClient.get("/scripts/running");
    return data;
  },

  async getRecent(limit: number = 50): Promise<ScriptRun[]> {
    const { data } = await apiClient.get("/scripts/recent", { params: { limit } });
    return data;
  },
};

export default scriptsApi;
