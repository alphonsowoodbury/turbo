import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import axios from "axios";

const API_BASE = "http://localhost:8001/api/v1";

interface Form {
  id: string;
  title: string;
  description?: string;
  schema: any;
  status: string;
  issue_id?: string;
  document_id?: string;
  project_id?: string;
  created_by: string;
  created_by_type: string;
  on_submit?: any;
  created_at: string;
  updated_at: string;
}

interface FormResponse {
  id: string;
  form_id: string;
  responses: Record<string, any>;
  responded_by: string;
  responded_by_type: string;
  is_complete: boolean;
  completed_at?: string;
  created_at: string;
  updated_at: string;
}

// Get forms for an issue
export function useIssueForms(issueId: string | undefined) {
  return useQuery<Form[]>({
    queryKey: ["forms", "issue", issueId],
    queryFn: async () => {
      if (!issueId) return [];
      const response = await axios.get(`${API_BASE}/forms/issues/${issueId}/forms`);
      return response.data;
    },
    enabled: !!issueId,
  });
}

// Get a specific form
export function useForm(formId: string | undefined) {
  return useQuery<Form>({
    queryKey: ["forms", formId],
    queryFn: async () => {
      if (!formId) throw new Error("Form ID is required");
      const response = await axios.get(`${API_BASE}/forms/${formId}`);
      return response.data;
    },
    enabled: !!formId,
  });
}

// Get responses for a form
export function useFormResponses(formId: string | undefined) {
  return useQuery<FormResponse[]>({
    queryKey: ["formResponses", formId],
    queryFn: async () => {
      if (!formId) return [];
      const response = await axios.get(`${API_BASE}/forms/${formId}/responses`);
      return response.data;
    },
    enabled: !!formId,
  });
}

// Create a new form
export function useCreateForm() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (formData: any) => {
      const response = await axios.post(`${API_BASE}/forms/`, formData);
      return response.data;
    },
    onSuccess: (data, variables) => {
      // Invalidate relevant queries
      if (variables.issue_id) {
        queryClient.invalidateQueries({ queryKey: ["forms", "issue", variables.issue_id] });
      }
      if (variables.document_id) {
        queryClient.invalidateQueries({ queryKey: ["forms", "document", variables.document_id] });
      }
      if (variables.project_id) {
        queryClient.invalidateQueries({ queryKey: ["forms", "project", variables.project_id] });
      }
    },
  });
}

// Submit a form response
export function useSubmitFormResponse() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ formId, data }: { formId: string; data: any }) => {
      const response = await axios.post(`${API_BASE}/forms/${formId}/responses`, data);
      return response.data;
    },
    onSuccess: (data, variables) => {
      queryClient.invalidateQueries({ queryKey: ["formResponses", variables.formId] });
      queryClient.invalidateQueries({ queryKey: ["forms", variables.formId] });
    },
  });
}
