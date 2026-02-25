import { apiClient } from "./client";

export interface MyQueueActionApproval {
  id: string;
  action_type: string;
  entity_type: string;
  entity_id: string;
  requested_by: string;
  status: string;
  created_at: string;
}

export interface MyQueueReviewRequest {
  id: string;
  title: string;
  description: string;
  request_type: string;
  priority: string;
  staff_id: string;
  created_at: string;
}

export interface MyQueueIssue {
  id: string;
  title: string;
  description?: string;
  type: string;
  status: string;
  priority: string;
  created_at: string;
}

export interface MyQueueMilestone {
  id: string;
  name: string;
  description?: string;
  status: string;
  due_date: string;
}

export interface MyQueueInitiative {
  id: string;
  name: string;
  description?: string;
  status: string;
  created_at: string;
}

export interface MyQueueCounts {
  action_approvals: number;
  assigned_issues: number;
  assigned_initiatives: number;
  assigned_milestones: number;
  review_requests: number;
  total: number;
}

export interface MyQueueResponse {
  action_approvals: MyQueueActionApproval[];
  review_requests: MyQueueReviewRequest[];
  assigned_issues: MyQueueIssue[];
  assigned_milestones: MyQueueMilestone[];
  assigned_initiatives: MyQueueInitiative[];
  counts: MyQueueCounts;
}

export async function fetchMyQueue(limit?: number): Promise<MyQueueResponse> {
  const params = limit ? { limit } : {};
  const { data } = await apiClient.get("/work-queue/my-queue", { params });
  return data;
}

export async function fetchMyQueueCounts(): Promise<MyQueueCounts> {
  const { data } = await apiClient.get("/work-queue/my-queue/counts");
  return data;
}

export async function fetchReviewRequests(limit?: number): Promise<any[]> {
  const params = limit ? { limit } : {};
  const { data } = await apiClient.get("/work-queue/review-requests", { params });
  return data;
}

export async function fetchBlockedIssues(limit?: number): Promise<any[]> {
  const params = limit ? { limit } : {};
  const { data } = await apiClient.get("/work-queue/blocked", { params });
  return data;
}

export async function refreshQueue(): Promise<void> {
  await apiClient.post("/work-queue/refresh");
}
