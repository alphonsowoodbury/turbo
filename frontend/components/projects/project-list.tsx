"use client";

import { useState } from "react";
import { useProjects } from "@/hooks/use-projects";
import { useWorkspace, getWorkspaceParams } from "@/hooks/use-workspace";
import { ProjectCard } from "./project-card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Loader2 } from "lucide-react";

export function ProjectList() {
  const [status, setStatus] = useState<string | undefined>(undefined);
  const { workspace, workCompany } = useWorkspace();

  // Build query params with workspace filtering
  const workspaceParams = getWorkspaceParams(workspace, workCompany);
  const queryParams = {
    status,
    ...workspaceParams
  };

  const { data: projects, isLoading, error } = useProjects(queryParams);

  if (isLoading) {
    return (
      <div className="flex h-64 items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex h-64 items-center justify-center">
        <div className="text-center">
          <p className="text-sm text-muted-foreground">
            Failed to load projects
          </p>
          <p className="mt-1 text-xs text-destructive">
            {error instanceof Error ? error.message : "Unknown error"}
          </p>
        </div>
      </div>
    );
  }

  const filteredProjects = projects || [];

  return (
    <div className="space-y-6">
      <Tabs defaultValue="all" className="w-full">
        <TabsList>
          <TabsTrigger value="all" onClick={() => setStatus(undefined)}>
            All
          </TabsTrigger>
          <TabsTrigger value="active" onClick={() => setStatus("active")}>
            Active
          </TabsTrigger>
          <TabsTrigger value="on_hold" onClick={() => setStatus("on_hold")}>
            On Hold
          </TabsTrigger>
          <TabsTrigger value="completed" onClick={() => setStatus("completed")}>
            Completed
          </TabsTrigger>
        </TabsList>

        <TabsContent value={status || "all"} className="mt-6">
          {filteredProjects.length === 0 ? (
            <div className="flex h-64 items-center justify-center">
              <p className="text-sm text-muted-foreground">
                No projects found
              </p>
            </div>
          ) : (
            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
              {filteredProjects.map((project) => (
                <ProjectCard key={project.id} project={project} />
              ))}
            </div>
          )}
        </TabsContent>
      </Tabs>
    </div>
  );
}