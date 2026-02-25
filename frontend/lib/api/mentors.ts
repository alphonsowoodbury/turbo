import { apiClient } from "./client";

export interface Mentor {
  id: string;
  name: string;
  description: string;
  persona: string;
  workspace?: string;
  work_company?: string;
  is_active?: boolean;
  context_preferences?: Record<string, unknown>;
  message_count?: number;
  created_at: string;
  updated_at: string;
}

export interface CreateMentorData {
  name: string;
  description: string;
  persona: string;
  workspace?: string;
  work_company?: string;
  is_active?: boolean;
}

export interface UpdateMentorData {
  name?: string;
  description?: string;
  persona?: string;
  workspace?: string;
  work_company?: string;
  is_active?: boolean;
}

export interface MentorMessage {
  id: string;
  content: string;
  role: "user" | "assistant";
  created_at: string;
}

export interface ConversationHistory {
  messages: MentorMessage[];
}

export interface SendMessageResponse {
  message: MentorMessage;
}

export async function fetchMentors(params?: {
  workspace?: string;
  work_company?: string;
  is_active?: boolean;
  limit?: number;
  offset?: number;
}): Promise<Mentor[]> {
  const { data } = await apiClient.get("/mentors/", { params });
  return data;
}

export async function fetchMentor(id: string): Promise<Mentor> {
  const { data } = await apiClient.get(`/mentors/${id}`);
  return data;
}

export async function createMentor(mentor: CreateMentorData): Promise<Mentor> {
  const { data } = await apiClient.post("/mentors/", mentor);
  return data;
}

export async function updateMentor(id: string, updates: UpdateMentorData): Promise<Mentor> {
  const { data } = await apiClient.put(`/mentors/${id}`, updates);
  return data;
}

export async function deleteMentor(id: string): Promise<void> {
  await apiClient.delete(`/mentors/${id}`);
}

export async function updateMessage(mentorId: string, messageId: string, content: string): Promise<MentorMessage> {
  const { data } = await apiClient.put(`/mentors/${mentorId}/messages/${messageId}`, { content });
  return data;
}

export async function deleteMessage(mentorId: string, messageId: string): Promise<void> {
  await apiClient.delete(`/mentors/${mentorId}/messages/${messageId}`);
}

export async function clearConversation(mentorId: string): Promise<void> {
  await apiClient.delete(`/mentors/${mentorId}/conversation`);
}

export async function fetchConversation(
  mentorId: string,
  params?: { limit?: number; offset?: number }
): Promise<ConversationHistory> {
  const { data } = await apiClient.get(`/mentors/${mentorId}/conversation`, { params });
  return data;
}

export async function sendMessage(mentorId: string, content: string): Promise<SendMessageResponse> {
  const { data } = await apiClient.post(`/mentors/${mentorId}/messages`, { content });
  return { message: data };
}
