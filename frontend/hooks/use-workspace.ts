"use client";

import { create } from "zustand";
import { persist } from "zustand/middleware";

export type Workspace = "all" | "personal" | "freelance" | "work";

interface WorkspaceState {
  workspace: Workspace;
  workCompany: string | null;
  setWorkspace: (workspace: Workspace, workCompany?: string | null) => void;
}

export const useWorkspace = create<WorkspaceState>()(
  persist(
    (set) => ({
      workspace: "all",
      workCompany: null,
      setWorkspace: (workspace, workCompany = null) =>
        set({ workspace, workCompany: workspace === "work" ? workCompany : null }),
    }),
    {
      name: "turbo-workspace",
    }
  )
);

/**
 * Get workspace label for display
 */
export function getWorkspaceLabel(workspace: Workspace, workCompany?: string | null): string {
  switch (workspace) {
    case "all":
      return "All Work";
    case "personal":
      return "Personal";
    case "freelance":
      return "Freelance";
    case "work":
      return workCompany || "Corporate Work";
    default:
      return "All Work";
  }
}

/**
 * Get workspace query params for API calls
 */
export function getWorkspaceParams(workspace: Workspace, workCompany?: string | null) {
  const params: Record<string, string> = {};

  if (workspace !== "all") {
    params.workspace = workspace;
    if (workspace === "work" && workCompany) {
      params.work_company = workCompany;
    }
  }

  return params;
}
