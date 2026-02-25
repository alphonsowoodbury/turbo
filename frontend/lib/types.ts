// ---------------------------------------------------------------------------
// Utility types (string unions)
// ---------------------------------------------------------------------------

export type ProjectStatus = "active" | "on_hold" | "completed" | "archived";

export type Priority = "low" | "medium" | "high" | "critical";

export type IssueStatus = "open" | "in_progress" | "review" | "testing" | "ready" | "closed";

export type IssueType = "bug" | "feature" | "enhancement" | "task" | "discovery";

export type InitiativeStatus = "proposed" | "active" | "completed" | "cancelled";

export type MilestoneStatus = "planned" | "active" | "completed" | "cancelled";

export type EntityType = "project" | "issue" | "milestone" | "initiative" | "document" | "note";

export type EventType = "deadline" | "milestone" | "meeting" | "reminder" | "event";

export type StandaloneEventCategory =
  | "personal"
  | "work"
  | "meeting"
  | "deadline"
  | "appointment"
  | "reminder"
  | "holiday"
  | "other";

export type ActionStatus = "pending" | "approved" | "denied" | "expired";

export type ActionRiskLevel = "low" | "medium" | "high" | "critical";

export type BlueprintCategory = "project" | "issue" | "workflow" | "template";

// ---------------------------------------------------------------------------
// Project
// ---------------------------------------------------------------------------

export interface Project {
  id: string;
  name: string;
  description?: string;
  status?: ProjectStatus;
  priority?: Priority;
  completion_percentage?: number;
  workspace?: "personal" | "freelance" | "work";
  work_company?: string;
  project_key?: string;
  is_archived?: boolean;
  repository_path?: string;
  created_at: string;
  updated_at: string;
}

export interface ProjectCreate {
  name: string;
  description?: string;
  status?: string;
  priority?: string;
  workspace?: string;
  work_company?: string;
  project_key?: string;
  completion_percentage?: number;
  is_archived?: boolean;
  repository_path?: string;
}

export interface ProjectUpdate {
  name?: string;
  description?: string;
  status?: string;
  priority?: string;
  completion_percentage?: number;
  workspace?: string;
  work_company?: string;
}

// ---------------------------------------------------------------------------
// Issue
// ---------------------------------------------------------------------------

export interface Issue {
  id: string;
  title: string;
  description?: string;
  status?: IssueStatus;
  priority?: Priority;
  type?: IssueType;
  project_id?: string;
  assignee?: string;
  due_date?: string;
  issue_key?: string;
  created_at: string;
  updated_at: string;
}

export interface IssueCreate {
  title: string;
  description?: string;
  type: string;
  priority: string;
  project_id?: string;
  assignee?: string;
  due_date?: string;
  workspace?: string;
}

export interface IssueUpdate {
  title?: string;
  description?: string;
  status?: string;
  priority?: string;
  type?: string;
  assignee?: string;
  due_date?: string;
}

// ---------------------------------------------------------------------------
// Milestone
// ---------------------------------------------------------------------------

export interface Milestone {
  id: string;
  name: string;
  description: string;
  status: string;
  start_date?: string;
  due_date: string;
  project_id: string;
  milestone_key: string;
  milestone_number: number;
  issue_count: number;
  tag_count: number;
  document_count: number;
  created_at: string;
  updated_at: string;
}

export interface MilestoneCreate {
  name: string;
  description: string;
  status?: string;
  start_date?: string;
  due_date: string;
  project_id: string;
  issue_ids?: string[];
  tag_ids?: string[];
  document_ids?: string[];
}

export interface MilestoneUpdate {
  name?: string;
  description?: string;
  status?: string;
  start_date?: string;
  due_date?: string;
  issue_ids?: string[];
  tag_ids?: string[];
  document_ids?: string[];
}

// ---------------------------------------------------------------------------
// Initiative
// ---------------------------------------------------------------------------

export interface Initiative {
  id: string;
  name: string;
  description: string;
  status: string;
  start_date?: string;
  target_date?: string;
  project_id?: string;
  initiative_key?: string;
  initiative_number?: number;
  issue_count: number;
  tag_count: number;
  document_count: number;
  created_at: string;
  updated_at: string;
}

export interface InitiativeCreate {
  name: string;
  description: string;
  status?: string;
  start_date?: string;
  target_date?: string;
  project_id?: string;
  issue_ids?: string[];
  tag_ids?: string[];
  document_ids?: string[];
}

export interface InitiativeUpdate {
  name?: string;
  description?: string;
  status?: string;
  start_date?: string;
  target_date?: string;
  project_id?: string;
  issue_ids?: string[];
  tag_ids?: string[];
  document_ids?: string[];
}

// ---------------------------------------------------------------------------
// Note
// ---------------------------------------------------------------------------

export interface Note {
  id: string;
  title: string;
  content?: string;
  workspace: string;
  work_company?: string;
  is_archived: boolean;
  tags: TagSummary[];
  created_at: string;
  updated_at: string;
}

export interface NoteCreate {
  title: string;
  content?: string;
  workspace?: string;
  work_company?: string;
  tag_ids?: string[];
}

export interface NoteUpdate {
  title?: string;
  content?: string;
  workspace?: string;
  work_company?: string;
  is_archived?: boolean;
  tag_ids?: string[];
}

// ---------------------------------------------------------------------------
// Mentor
// ---------------------------------------------------------------------------

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

// ---------------------------------------------------------------------------
// Document
// ---------------------------------------------------------------------------

export interface Document {
  id: string;
  title: string;
  content: string;
  doc_type?: string;
  format?: string;
  project_id?: string;
  created_at: string;
  updated_at: string;
}

// ---------------------------------------------------------------------------
// Tag
// ---------------------------------------------------------------------------

export interface Tag {
  id: string;
  name: string;
  color: string;
  description?: string;
  created_at: string;
  updated_at: string;
}

export interface TagCreate {
  name: string;
  color: string;
  description?: string;
}

export interface TagUpdate {
  name?: string;
  color?: string;
  description?: string;
}

export interface TagSummary {
  id: string;
  name: string;
  color: string;
}

// ---------------------------------------------------------------------------
// Comment
// ---------------------------------------------------------------------------

export interface Comment {
  id: string;
  content: string;
  author_type: "user" | "ai";
  author_name?: string;
  entity_type: string;
  entity_id: string;
  created_at: string;
}

export interface CommentCreate {
  content: string;
  entity_type: string;
  entity_id: string;
  author_type?: string;
  author_name?: string;
}

export interface CommentUpdate {
  content?: string;
}

// ---------------------------------------------------------------------------
// Calendar Event (aggregate events from multiple sources)
// ---------------------------------------------------------------------------

export interface CalendarEvent {
  id: string;
  title: string;
  description?: string;
  date: string;
  event_type: string;
  category: string;
  status?: string;
  priority?: string;
  project_id?: string;
  project_name?: string;
  url?: string;
  color?: string;
  icon?: string;
}

export interface CalendarEventsResponse {
  events: CalendarEvent[];
  total: number;
  start_date?: string;
  end_date?: string;
}

// ---------------------------------------------------------------------------
// Blueprint
// ---------------------------------------------------------------------------

export interface Blueprint {
  id: string;
  name: string;
  description: string;
  category: string;
  content: Record<string, unknown>;
  version: string;
  is_active: boolean;
  assigned_to_type?: string;
  assigned_to_id?: string;
  created_at: string;
  updated_at: string;
}

export interface BlueprintCreate {
  name: string;
  description: string;
  category: string;
  content?: Record<string, unknown>;
  version: string;
  is_active?: boolean;
  assigned_to_type?: string;
  assigned_to_id?: string;
}

export interface BlueprintUpdate {
  name?: string;
  description?: string;
  category?: string;
  content?: Record<string, unknown>;
  version?: string;
  is_active?: boolean;
  assigned_to_type?: string;
  assigned_to_id?: string;
}

export interface BlueprintSummary {
  id: string;
  name: string;
  category: string;
  description: string;
  version: string;
  is_active: boolean;
}

// ---------------------------------------------------------------------------
// Action Approval
// ---------------------------------------------------------------------------

export interface ActionApproval {
  id: string;
  action_type: string;
  action_description: string;
  risk_level: string;
  action_params: Record<string, unknown>;
  entity_type: string;
  entity_id: string;
  entity_title?: string;
  ai_reasoning?: string;
  ai_comment_id?: string;
  status: string;
  approved_at?: string;
  approved_by?: string;
  denied_at?: string;
  denied_by?: string;
  denial_reason?: string;
  executed_at?: string;
  execution_result?: Record<string, unknown>;
  execution_error?: string;
  executed_by_subagent: boolean;
  subagent_name?: string;
  auto_execute: boolean;
  auto_executed_at?: string;
  created_at: string;
  updated_at: string;
  expires_at?: string;
}

export interface ApproveActionRequest {
  reason?: string;
}

export interface DenyActionRequest {
  reason: string;
}
