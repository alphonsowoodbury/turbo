import { apiClient } from "./client";
import type { Project, ProjectCreate, ProjectUpdate } from "@/lib/types";

export const projectsApi = {
  async list(params?: {
    skip?: number;
    limit?: number;
    status?: string;
    priority?: string;
    workspace?: string;
    work_company?: string;
  }): Promise<Project[]> {
    const { data } = await apiClient.get("/projects/", { params });
    return data;
  },

  async get(id: string): Promise<Project> {
    const { data } = await apiClient.get(`/projects/${id}`);
    return data;
  },

  async getWithStats(id: string): Promise<Project> {
    const { data } = await apiClient.get(`/projects/${id}/with-stats`);
    return data;
  },

  async create(project: ProjectCreate): Promise<Project> {
    const { data } = await apiClient.post("/projects/", project);
    return data;
  },

  async update(id: string, updates: ProjectUpdate): Promise<Project> {
    const { data } = await apiClient.put(`/projects/${id}`, updates);
    return data;
  },

  async delete(id: string): Promise<void> {
    await apiClient.delete(`/projects/${id}`);
  },

  async getIssues(id: string): Promise<any[]> {
    const { data } = await apiClient.get(`/projects/${id}/issues`);
    return data;
  },
};
