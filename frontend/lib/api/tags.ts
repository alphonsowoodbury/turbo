import { apiClient } from "./client";
import type { Tag, TagCreate, TagUpdate } from "@/lib/types";

export const tagsApi = {
  async list(params?: Record<string, unknown>): Promise<Tag[]> {
    const { data } = await apiClient.get("/tags/", { params });
    return data;
  },

  async get(id: string): Promise<Tag> {
    const { data } = await apiClient.get(`/tags/${id}`);
    return data;
  },

  async create(item: TagCreate): Promise<Tag> {
    const { data } = await apiClient.post("/tags/", item);
    return data;
  },

  async update(id: string, updates: TagUpdate): Promise<Tag> {
    const { data } = await apiClient.put(`/tags/${id}`, updates);
    return data;
  },

  async delete(id: string): Promise<void> {
    await apiClient.delete(`/tags/${id}`);
  },
};

export default tagsApi;
