import { apiClient } from "./client";

export interface Staff {
  id: string;
  handle: string;
  alias?: string;
  name: string;
  description: string;
  persona: string;
  role_type: "leadership" | "domain_expert";
  role_title?: string;
  is_leadership_role: boolean;
  monitoring_scope: {
    entity_types: string[];
    tags: string[];
    focus: string;
    metrics: string[];
  };
  capabilities: string[];
  allowed_tools: string[];
  is_active: boolean;
  overall_rating?: number;
  performance_metrics: {
    completed_tasks: number;
    avg_response_time_hours: number;
    quality_score: number;
    completion_rate: number;
    total_assignments: number;
  };
  created_at: string;
  updated_at: string;
}

export interface StaffMessage {
  id: string;
  content: string;
  role: "user" | "assistant";
  created_at: string;
}

export interface StaffConversationHistory {
  messages: StaffMessage[];
}

export async function fetchStaff(params?: {
  role_type?: "leadership" | "domain_expert";
  is_active?: boolean;
  limit?: number;
  offset?: number;
}): Promise<Staff[]> {
  const { data } = await apiClient.get("/staff/", { params });
  return data;
}

export async function fetchStaffMember(id: string): Promise<Staff> {
  const { data } = await apiClient.get(`/staff/${id}`);
  return data;
}

export interface StaffProfile {
  staff: Staff;
  computed_metrics: Record<string, number>;
  assigned_review_requests: Array<{
    id: string;
    title: string;
    description?: string;
    request_type: string;
    priority: string;
    staff_id: string;
    created_at: string;
  }>;
  recent_activity: Array<{
    id: string;
    type: string;
    description: string;
    created_at: string;
  }>;
  assigned_issues_count: number;
  pending_approvals_count: number;
}

export async function fetchStaffProfile(id: string): Promise<StaffProfile> {
  const { data } = await apiClient.get(`/staff/${id}/profile`);
  return data;
}

export async function fetchStaffByHandle(handle: string): Promise<Staff> {
  const { data } = await apiClient.get(`/staff/handle/${handle}`);
  return data;
}

export async function fetchStaffConversation(
  id: string,
  params?: { limit?: number; offset?: number }
): Promise<StaffConversationHistory> {
  const { data } = await apiClient.get(`/staff/${id}/conversation`, { params });
  return data;
}

export async function sendStaffMessage(id: string, content: string): Promise<StaffMessage> {
  const { data } = await apiClient.post(`/staff/${id}/messages`, { content });
  return data;
}

export async function createStaff(staff: Partial<Staff>): Promise<Staff> {
  const { data } = await apiClient.post("/staff/", staff);
  return data;
}

export async function updateStaff(id: string, updates: Partial<Staff>): Promise<Staff> {
  const { data } = await apiClient.put(`/staff/${id}`, updates);
  return data;
}

export async function deleteStaff(id: string): Promise<void> {
  await apiClient.delete(`/staff/${id}`);
}

export async function clearStaffConversation(id: string): Promise<void> {
  await apiClient.delete(`/staff/${id}/conversation`);
}
