import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import axios from "axios";

const API_BASE = "http://localhost:8001/api/v1";

interface Document {
  id: string;
  title: string;
  content: string;
  type: string;
  format: string;
  version?: string;
  author?: string;
  project_id: string;
  created_at: string;
  updated_at: string;
}

interface CreateDocumentData {
  title: string;
  content: string;
  project_id: string;
  type?: string;
  format?: string;
  version?: string;
  author?: string;
}

interface UpdateDocumentData {
  title?: string;
  content?: string;
  type?: string;
  format?: string;
  version?: string;
  author?: string;
}

// Get all documents for a project
export function useProjectDocuments(projectId: string | undefined) {
  return useQuery<Document[]>({
    queryKey: ["documents", "project", projectId],
    queryFn: async () => {
      if (!projectId) return [];
      const response = await axios.get(`${API_BASE}/documents/`, {
        params: { project_id: projectId },
      });
      return response.data;
    },
    enabled: !!projectId,
  });
}

// Get a specific document
export function useDocument(documentId: string | undefined) {
  return useQuery<Document>({
    queryKey: ["documents", documentId],
    queryFn: async () => {
      if (!documentId) throw new Error("Document ID is required");
      const response = await axios.get(`${API_BASE}/documents/${documentId}`);
      return response.data;
    },
    enabled: !!documentId,
  });
}

// Get all documents
export function useDocuments(params?: {
  limit?: number;
  offset?: number;
  workspace?: string;
  work_company?: string;
}) {
  return useQuery<Document[]>({
    queryKey: ["documents", "all", params],
    queryFn: async () => {
      const response = await axios.get(`${API_BASE}/documents/`, {
        params,
      });
      return response.data;
    },
  });
}

// Search documents
export function useSearchDocuments(query: string | undefined) {
  return useQuery<Document[]>({
    queryKey: ["documents", "search", query],
    queryFn: async () => {
      if (!query) return [];
      const response = await axios.get(`${API_BASE}/documents/search`, {
        params: { query },
      });
      return response.data;
    },
    enabled: !!query && query.length > 0,
  });
}

// Create a new document
export function useCreateDocument() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (data: CreateDocumentData) => {
      const response = await axios.post(`${API_BASE}/documents/`, data);
      return response.data;
    },
    onSuccess: (data, variables) => {
      // Invalidate documents for the project
      queryClient.invalidateQueries({ queryKey: ["documents", "project", variables.project_id] });
      queryClient.invalidateQueries({ queryKey: ["documents", "all"] });
    },
  });
}

// Update a document
export function useUpdateDocument() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ documentId, data }: { documentId: string; data: UpdateDocumentData }) => {
      const response = await axios.put(`${API_BASE}/documents/${documentId}`, data);
      return response.data;
    },
    onSuccess: (data) => {
      // Invalidate relevant queries
      queryClient.invalidateQueries({ queryKey: ["documents", data.id] });
      queryClient.invalidateQueries({ queryKey: ["documents", "project", data.project_id] });
      queryClient.invalidateQueries({ queryKey: ["documents", "all"] });
    },
  });
}

// Delete a document
export function useDeleteDocument() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (documentId: string) => {
      await axios.delete(`${API_BASE}/documents/${documentId}`);
    },
    onSuccess: () => {
      // Invalidate all document queries
      queryClient.invalidateQueries({ queryKey: ["documents"] });
    },
  });
}

// Export a document
export function useExportDocument() {
  return useMutation({
    mutationFn: async ({ documentId, format }: { documentId: string; format: string }) => {
      const response = await axios.get(`${API_BASE}/documents/${documentId}/export`, {
        params: { format },
        responseType: "blob",
      });
      return { data: response.data, format };
    },
  });
}
