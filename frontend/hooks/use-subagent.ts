/**
 * React Hook for invoking Turbo AI Subagents
 *
 * Two agent sets:
 * - turbo: In-app agents for productivity (project management, issue triage, etc.)
 * - turbodev: External development agents (code editing, refactoring) - not exposed in UI
 */

import { useMutation, useQuery } from "@tanstack/react-query";
import { useState } from "react";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8001";

export interface SubagentRequest {
  agent: string;
  prompt: string;
  context?: Record<string, any>;
  agent_set?: "turbo" | "turbodev";
}

export interface SubagentAction {
  type: string;
  [key: string]: any;
}

export interface SubagentResponse {
  agent: string;
  response: string;
  actions?: SubagentAction[];
  error?: string;
}

export interface Subagent {
  name: string;
  description: string;
  capabilities: string[];
  agent_set: "turbo" | "turbodev";
}

/**
 * Hook to invoke a specific subagent
 */
export function useSubagent(agentName: string) {
  const [isStreaming, setIsStreaming] = useState(false);
  const [streamedResponse, setStreamedResponse] = useState("");

  const mutation = useMutation({
    mutationFn: async (request: Omit<SubagentRequest, "agent">) => {
      const response = await fetch(`${API_BASE}/api/v1/subagents/invoke`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          agent: agentName,
          ...request,
        }),
      });

      if (!response.ok) {
        throw new Error(`Subagent invocation failed: ${response.statusText}`);
      }

      return response.json() as Promise<SubagentResponse>;
    },
  });

  const invoke = async (
    prompt: string,
    context?: Record<string, any>
  ): Promise<SubagentResponse> => {
    return mutation.mutateAsync({ prompt, context, agent_set: "turbo" });
  };

  return {
    invoke,
    isLoading: mutation.isPending,
    error: mutation.error,
    data: mutation.data,
    isStreaming,
    streamedResponse,
  };
}

/**
 * Hook to list available subagents
 */
export function useSubagents(agentSet: "turbo" | "turbodev" = "turbo") {
  return useQuery({
    queryKey: ["subagents", agentSet],
    queryFn: async () => {
      const response = await fetch(
        `${API_BASE}/api/v1/subagents/list?agent_set=${agentSet}`
      );

      if (!response.ok) {
        throw new Error("Failed to fetch subagents");
      }

      const data = await response.json();
      return data.subagents as Subagent[];
    },
  });
}

/**
 * Hook for quick subagent invocation with any agent
 */
export function useInvokeSubagent() {
  return useMutation({
    mutationFn: async (request: SubagentRequest) => {
      const response = await fetch(`${API_BASE}/api/v1/subagents/invoke`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          ...request,
          agent_set: request.agent_set || "turbo",
        }),
      });

      if (!response.ok) {
        throw new Error(`Subagent invocation failed: ${response.statusText}`);
      }

      return response.json() as Promise<SubagentResponse>;
    },
  });
}

/**
 * Utility hook for common subagent operations
 */
export function useSubagentHelpers() {
  const { mutateAsync: invoke } = useInvokeSubagent();

  const triageIssue = async (issueId: string) => {
    return invoke({
      agent: "issue-triager",
      prompt: "Analyze this issue and suggest priority, type, tags, and any dependencies.",
      context: { issue_id: issueId },
    });
  };

  const generateProjectHealth = async (projectId: string) => {
    return invoke({
      agent: "project-manager",
      prompt: "Generate a comprehensive health report for this project including status, risks, and recommendations.",
      context: { project_id: projectId },
    });
  };

  const analyzeDocument = async (documentId: string) => {
    return invoke({
      agent: "doc-curator",
      prompt: "Review this document for clarity, completeness, and suggest improvements.",
      context: { document_id: documentId },
    });
  };

  const suggestSchedule = async (issueIds: string[]) => {
    return invoke({
      agent: "task-scheduler",
      prompt: "Analyze these issues and suggest an optimal schedule considering priorities and dependencies.",
      context: { issue_ids: issueIds },
    });
  };

  const findConnections = async (entityType: string, entityId: string) => {
    return invoke({
      agent: "knowledge-connector",
      prompt: "Find all related entities and suggest meaningful connections.",
      context: { entity_type: entityType, entity_id: entityId },
    });
  };

  const optimizeResume = async (resumeId: string, jobDescription?: string) => {
    return invoke({
      agent: "career-coach",
      prompt: jobDescription
        ? "Analyze this resume against the job description and suggest improvements."
        : "Review this resume and suggest general improvements.",
      context: { resume_id: resumeId, job_description: jobDescription },
    });
  };

  const suggestReadingOrder = async (filters?: Record<string, any>) => {
    return invoke({
      agent: "learning-curator",
      prompt: "Analyze my reading list and suggest an optimal reading order based on my goals and current skills.",
      context: filters,
    });
  };

  const extractActionItems = async (meetingNotes: string) => {
    return invoke({
      agent: "meeting-facilitator",
      prompt: "Extract action items from these meeting notes and suggest how to track them.",
      context: { notes: meetingNotes },
    });
  };

  const manageDiscovery = async (issueId: string, action: "analyze" | "decide" | "convert") => {
    const prompts = {
      analyze: "Analyze the research findings and suggest next steps.",
      decide: "Help decide if this discovery is ready to move to approved or should be parked/declined.",
      convert: "Convert this discovery into actionable feature work or initiatives.",
    };

    return invoke({
      agent: "discovery-guide",
      prompt: prompts[action],
      context: { issue_id: issueId },
    });
  };

  const reviewBlueprint = async (blueprintId: string) => {
    return invoke({
      agent: "blueprint-architect",
      prompt: "Review this blueprint and suggest improvements or related patterns.",
      context: { blueprint_id: blueprintId },
    });
  };

  return {
    triageIssue,
    generateProjectHealth,
    analyzeDocument,
    suggestSchedule,
    findConnections,
    optimizeResume,
    suggestReadingOrder,
    extractActionItems,
    manageDiscovery,
    reviewBlueprint,
  };
}
