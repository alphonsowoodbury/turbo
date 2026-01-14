"use client";

import { useState, useMemo, useEffect, Suspense } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { PageLayout } from "@/components/layout/page-layout";
import { useMilestones } from "@/hooks/use-milestones";
import { useProjects, useProject } from "@/hooks/use-projects";
import { useWorkspace, getWorkspaceParams } from "@/hooks/use-workspace";
import { CreateMilestoneDialog } from "@/components/milestones/create-milestone-dialog";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Calendar, Plus, Filter, X } from "lucide-react";
import { cn } from "@/lib/utils";
import { formatDistanceToNow, format } from "date-fns";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

const milestoneStatusColors = {
  planned: "bg-gray-500/10 text-gray-500 hover:bg-gray-500/20",
  in_progress: "bg-blue-500/10 text-blue-500 hover:bg-blue-500/20",
  completed: "bg-green-500/10 text-green-500 hover:bg-green-500/20",
  cancelled: "bg-red-500/10 text-red-500 hover:bg-red-500/20",
};

function MilestonesContent() {
  const searchParams = useSearchParams();
  const projectIdFromUrl = searchParams.get("project_id");

  const [createDialogOpen, setCreateDialogOpen] = useState(false);
  const [showFilters, setShowFilters] = useState(false);
  const [selectedProject, setSelectedProject] = useState<string>("all");
  const [selectedStatus, setSelectedStatus] = useState<string>("all");
  const [groupBy, setGroupBy] = useState<string>("none");

  const { workspace, workCompany } = useWorkspace();
  const workspaceParams = getWorkspaceParams(workspace, workCompany);

  const { data: milestones, isLoading, error } = useMilestones(workspaceParams);
  const { data: projects } = useProjects(workspaceParams);
  const { data: filteredProject } = useProject(projectIdFromUrl || null);

  // Apply URL filter on mount
  useEffect(() => {
    if (projectIdFromUrl) {
      setSelectedProject(projectIdFromUrl);
      setShowFilters(true);
    }
  }, [projectIdFromUrl]);

  // Apply filters
  const filteredMilestones = useMemo(() => {
    if (!milestones) return [];

    let filtered = milestones;

    if (selectedProject !== "all") {
      filtered = filtered.filter((m) => m.project_id === selectedProject);
    }

    if (selectedStatus !== "all") {
      filtered = filtered.filter((m) => m.status === selectedStatus);
    }

    return filtered;
  }, [milestones, selectedProject, selectedStatus]);

  // Group milestones
  const groupedMilestones = useMemo(() => {
    if (groupBy === "none") {
      return { "All Milestones": filteredMilestones };
    }

    const groups: Record<string, typeof filteredMilestones> = {};

    filteredMilestones.forEach((milestone) => {
      let key = "";

      if (groupBy === "project") {
        const project = projects?.find((p) => p.id === milestone.project_id);
        key = project?.name || "Unknown Project";
      } else if (groupBy === "status") {
        key = milestone.status.replace("_", " ");
      }

      if (!groups[key]) {
        groups[key] = [];
      }
      groups[key].push(milestone);
    });

    return groups;
  }, [filteredMilestones, groupBy, projects]);

  const hasActiveFilters = selectedProject !== "all" || selectedStatus !== "all";

  const clearFilters = () => {
    setSelectedProject("all");
    setSelectedStatus("all");
  };

  return (
    <PageLayout
      title="Milestones"
      isLoading={isLoading}
      error={error}
      breadcrumbs={filteredProject ? [{ label: filteredProject.name, href: `/projects/${filteredProject.id}` }] : undefined}
    >
      <div className="flex-1 p-6">
        {/* Controls Bar */}
        <div className="mb-4 flex items-center justify-between">
          <Button onClick={() => setCreateDialogOpen(true)}>
            <Plus className="h-4 w-4 mr-2" />
            New Milestone
          </Button>
          <div className="flex items-center gap-2">
            <Button
              variant={showFilters ? "secondary" : "outline"}
              size="sm"
              onClick={() => setShowFilters(!showFilters)}
            >
              <Filter className="h-4 w-4 mr-2" />
              Filter
              {hasActiveFilters && (
                <Badge variant="secondary" className="ml-2 h-4 px-1 text-[10px]">
                  {[selectedProject !== "all", selectedStatus !== "all"].filter(Boolean).length}
                </Badge>
              )}
            </Button>
            {hasActiveFilters && (
              <Button variant="ghost" size="sm" onClick={clearFilters}>
                <X className="h-4 w-4 mr-1" />
                Clear
              </Button>
            )}
            <span className="text-sm text-muted-foreground">Group by:</span>
            <Select value={groupBy} onValueChange={setGroupBy}>
              <SelectTrigger className="w-32 h-8">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="none">None</SelectItem>
                <SelectItem value="project">Project</SelectItem>
                <SelectItem value="status">Status</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </div>

        {/* Filter Controls */}
        {showFilters && (
          <Card className="mb-4">
            <CardContent className="pt-6">
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <label className="text-sm font-medium">Project</label>
                  <Select value={selectedProject} onValueChange={setSelectedProject}>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="all">All Projects</SelectItem>
                      {projects?.map((project) => (
                        <SelectItem key={project.id} value={project.id}>
                          {project.name}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>

                <div className="space-y-2">
                  <label className="text-sm font-medium">Status</label>
                  <Select value={selectedStatus} onValueChange={setSelectedStatus}>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="all">All Statuses</SelectItem>
                      <SelectItem value="planned">Planned</SelectItem>
                      <SelectItem value="in_progress">In Progress</SelectItem>
                      <SelectItem value="completed">Completed</SelectItem>
                      <SelectItem value="cancelled">Cancelled</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>
            </CardContent>
          </Card>
        )}

        {filteredMilestones.length > 0 ? (
          <div className="space-y-6">
            {Object.entries(groupedMilestones).map(([groupName, groupMilestones]) => (
              <div key={groupName}>
                {groupBy !== "none" && (
                  <h3 className="mb-3 text-sm font-semibold text-muted-foreground capitalize">
                    {groupName} ({groupMilestones.length})
                  </h3>
                )}
                <div className="space-y-3">
                  {groupMilestones.map((milestone) => (
                    <Link key={milestone.id} href={`/milestones/${milestone.id}`}>
                      <Card className="hover:border-primary/50 cursor-pointer transition-colors">
                        <CardContent className="pt-6">
                          <div className="flex items-start justify-between gap-4">
                            <div className="flex-1 space-y-1">
                              <h3 className="font-semibold">{milestone.name}</h3>
                              <p className="text-sm text-muted-foreground line-clamp-2">
                                {milestone.description}
                              </p>
                              <div className="flex items-center gap-2 text-xs text-muted-foreground">
                                <Calendar className="h-3 w-3" />
                                <span>
                                  Due {format(new Date(milestone.due_date), "MMM d, yyyy")}
                                </span>
                                <span>•</span>
                                <span>
                                  {milestone.issue_count} {milestone.issue_count === 1 ? "issue" : "issues"}
                                </span>
                                <span>•</span>
                                <span>
                                  Updated {formatDistanceToNow(new Date(milestone.updated_at))}{" "}
                                  ago
                                </span>
                              </div>
                            </div>
                            <div className="flex gap-2">
                              <Badge
                                variant="secondary"
                                className={cn(
                                  "text-xs capitalize",
                                  milestoneStatusColors[milestone.status]
                                )}
                              >
                                {milestone.status.replace("_", " ")}
                              </Badge>
                            </div>
                          </div>
                        </CardContent>
                      </Card>
                    </Link>
                  ))}
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="flex h-64 items-center justify-center">
            <div className="text-center">
              <p className="text-sm text-muted-foreground">
                {milestones && milestones.length > 0
                  ? "No milestones match the current filters."
                  : "No milestones found. Create one to get started!"}
              </p>
              {hasActiveFilters && milestones && milestones.length > 0 && (
                <Button
                  variant="outline"
                  size="sm"
                  className="mt-4"
                  onClick={clearFilters}
                >
                  Clear Filters
                </Button>
              )}
            </div>
          </div>
        )}
      </div>

      <CreateMilestoneDialog
        open={createDialogOpen}
        onOpenChange={setCreateDialogOpen}
      />
    </PageLayout>
  );
}

export default function MilestonesPage() {
  return (
    <Suspense fallback={<PageLayout title="Milestones" isLoading={true} error={null}><div /></PageLayout>}>
      <MilestonesContent />
    </Suspense>
  );
}