"use client";

import { useState, useMemo } from "react";
import Link from "next/link";
import { PageLayout } from "@/components/layout/page-layout";
import { useIssues } from "@/hooks/use-issues";
import { useProjects } from "@/hooks/use-projects";
import { useWorkspace, getWorkspaceParams } from "@/hooks/use-workspace";
import { CreateIssueDialog } from "@/components/issues/create-issue-dialog";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Plus, Filter, X } from "lucide-react";
import { cn } from "@/lib/utils";
import { formatDistanceToNow } from "date-fns";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

const priorityColors = {
  low: "bg-blue-500/10 text-blue-500 hover:bg-blue-500/20",
  medium: "bg-yellow-500/10 text-yellow-500 hover:bg-yellow-500/20",
  high: "bg-orange-500/10 text-orange-500 hover:bg-orange-500/20",
  critical: "bg-red-500/10 text-red-500 hover:bg-red-500/20",
};

const statusColors = {
  open: "bg-green-500/10 text-green-500 hover:bg-green-500/20",
  in_progress: "bg-blue-500/10 text-blue-500 hover:bg-blue-500/20",
  review: "bg-purple-500/10 text-purple-500 hover:bg-purple-500/20",
  testing: "bg-orange-500/10 text-orange-500 hover:bg-orange-500/20",
  closed: "bg-gray-500/10 text-gray-500 hover:bg-gray-500/20",
};

export default function IssuesPage() {
  const [createDialogOpen, setCreateDialogOpen] = useState(false);
  const [showFilters, setShowFilters] = useState(false);
  const [selectedProject, setSelectedProject] = useState<string>("all");
  const [selectedStatus, setSelectedStatus] = useState<string>("all");
  const [selectedPriority, setSelectedPriority] = useState<string>("all");
  const [selectedType, setSelectedType] = useState<string>("all");
  const [groupBy, setGroupBy] = useState<string>("none");
  const [sortBy, setSortBy] = useState<string>("updated");

  const { workspace, workCompany } = useWorkspace();
  const workspaceParams = getWorkspaceParams(workspace, workCompany);

  const { data: issues, isLoading, error } = useIssues(workspaceParams);
  const { data: projects } = useProjects(workspaceParams);

  // Apply filters
  const filteredIssues = useMemo(() => {
    if (!issues) return [];

    let filtered = issues;

    if (selectedProject !== "all") {
      filtered = filtered.filter((i) => i.project_id === selectedProject);
    }

    if (selectedStatus !== "all") {
      filtered = filtered.filter((i) => i.status === selectedStatus);
    }

    if (selectedPriority !== "all") {
      filtered = filtered.filter((i) => i.priority === selectedPriority);
    }

    if (selectedType !== "all") {
      filtered = filtered.filter((i) => i.type === selectedType);
    }

    return filtered;
  }, [issues, selectedProject, selectedStatus, selectedPriority, selectedType]);

  // Sort issues
  const sortedIssues = useMemo(() => {
    const sorted = [...filteredIssues];

    switch (sortBy) {
      case "updated":
        return sorted.sort((a, b) => new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime());
      case "created":
        return sorted.sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime());
      case "priority":
        const priorityOrder = { critical: 0, high: 1, medium: 2, low: 3 };
        return sorted.sort((a, b) => priorityOrder[a.priority] - priorityOrder[b.priority]);
      case "title":
        return sorted.sort((a, b) => a.title.localeCompare(b.title));
      default:
        return sorted;
    }
  }, [filteredIssues, sortBy]);

  // Group issues
  const groupedIssues = useMemo(() => {
    if (groupBy === "none") {
      return { "All Issues": sortedIssues };
    }

    const groups: Record<string, typeof sortedIssues> = {};

    sortedIssues.forEach((issue) => {
      let key = "";

      if (groupBy === "project") {
        const project = projects?.find((p) => p.id === issue.project_id);
        key = project?.name || "Unknown Project";
      } else if (groupBy === "status") {
        key = issue.status.replace("_", " ");
      } else if (groupBy === "priority") {
        key = issue.priority;
      } else if (groupBy === "type") {
        key = issue.type;
      } else if (groupBy === "assignee") {
        key = issue.assignee || "Unassigned";
      }

      if (!groups[key]) {
        groups[key] = [];
      }
      groups[key].push(issue);
    });

    return groups;
  }, [sortedIssues, groupBy, projects]);

  const hasActiveFilters = selectedProject !== "all" || selectedStatus !== "all" || selectedPriority !== "all" || selectedType !== "all";

  const clearFilters = () => {
    setSelectedProject("all");
    setSelectedStatus("all");
    setSelectedPriority("all");
    setSelectedType("all");
  };

  return (
    <PageLayout
      title="Issues"
      isLoading={isLoading}
      error={error}
    >
      <div className="p-6">
        {/* Controls Bar */}
        <div className="mb-4 flex items-center justify-between">
          <Button onClick={() => setCreateDialogOpen(true)}>
            <Plus className="h-4 w-4 mr-2" />
            New Issue
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
                  {[selectedProject !== "all", selectedStatus !== "all", selectedPriority !== "all", selectedType !== "all"].filter(Boolean).length}
                </Badge>
              )}
            </Button>
            {hasActiveFilters && (
              <Button variant="ghost" size="sm" onClick={clearFilters}>
                <X className="h-4 w-4 mr-1" />
                Clear
              </Button>
            )}
            <span className="text-sm text-muted-foreground">Sort:</span>
            <Select value={sortBy} onValueChange={setSortBy}>
              <SelectTrigger className="w-32 h-8">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="updated">Updated</SelectItem>
                <SelectItem value="created">Created</SelectItem>
                <SelectItem value="priority">Priority</SelectItem>
                <SelectItem value="title">Title</SelectItem>
              </SelectContent>
            </Select>
            <span className="text-sm text-muted-foreground">Group:</span>
            <Select value={groupBy} onValueChange={setGroupBy}>
              <SelectTrigger className="w-32 h-8">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="none">None</SelectItem>
                <SelectItem value="project">Project</SelectItem>
                <SelectItem value="status">Status</SelectItem>
                <SelectItem value="priority">Priority</SelectItem>
                <SelectItem value="type">Type</SelectItem>
                <SelectItem value="assignee">Assignee</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </div>

        {/* Filter Controls */}
        {showFilters && (
          <Card className="mb-4">
            <CardContent className="pt-6">
              <div className="grid grid-cols-4 gap-4">
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
                      <SelectItem value="open">Open</SelectItem>
                      <SelectItem value="in_progress">In Progress</SelectItem>
                      <SelectItem value="review">Review</SelectItem>
                      <SelectItem value="testing">Testing</SelectItem>
                      <SelectItem value="closed">Closed</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                <div className="space-y-2">
                  <label className="text-sm font-medium">Priority</label>
                  <Select value={selectedPriority} onValueChange={setSelectedPriority}>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="all">All Priorities</SelectItem>
                      <SelectItem value="low">Low</SelectItem>
                      <SelectItem value="medium">Medium</SelectItem>
                      <SelectItem value="high">High</SelectItem>
                      <SelectItem value="critical">Critical</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                <div className="space-y-2">
                  <label className="text-sm font-medium">Type</label>
                  <Select value={selectedType} onValueChange={setSelectedType}>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="all">All Types</SelectItem>
                      <SelectItem value="feature">Feature</SelectItem>
                      <SelectItem value="bug">Bug</SelectItem>
                      <SelectItem value="task">Task</SelectItem>
                      <SelectItem value="enhancement">Enhancement</SelectItem>
                      <SelectItem value="documentation">Documentation</SelectItem>
                      <SelectItem value="discovery">Discovery</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>
            </CardContent>
          </Card>
        )}

        {filteredIssues.length > 0 ? (
          <div className="space-y-6">
            {Object.entries(groupedIssues).map(([groupName, groupIssues]) => (
              <div key={groupName}>
                {groupBy !== "none" && (
                  <h3 className="mb-3 text-sm font-semibold text-muted-foreground capitalize">
                    {groupName} ({groupIssues.length})
                  </h3>
                )}
                <div className="space-y-3">
                  {groupIssues.map((issue) => (
                    <Link key={issue.id} href={`/issues/${issue.id}`}>
                      <Card className="hover:border-primary/50 cursor-pointer transition-colors">
                        <CardContent className="pt-6">
                          <div className="flex items-start justify-between gap-4">
                            <div className="flex-1 space-y-1">
                              <h3 className="font-semibold">{issue.title}</h3>
                              <p className="text-sm text-muted-foreground line-clamp-2">
                                {issue.description}
                              </p>
                              <div className="flex items-center gap-2 text-xs text-muted-foreground">
                                <span>
                                  Updated {formatDistanceToNow(new Date(issue.updated_at))}{" "}
                                  ago
                                </span>
                                {issue.assignee && (
                                  <>
                                    <span>•</span>
                                    <span>Assigned to {issue.assignee}</span>
                                  </>
                                )}
                              </div>
                            </div>
                            <div className="flex gap-2">
                              <Badge variant="outline" className="text-xs capitalize">
                                {issue.type}
                              </Badge>
                              <Badge
                                variant="secondary"
                                className={cn(
                                  "text-xs capitalize",
                                  statusColors[issue.status]
                                )}
                              >
                                {issue.status.replace("_", " ")}
                              </Badge>
                              <Badge
                                variant="secondary"
                                className={cn("text-xs", priorityColors[issue.priority])}
                              >
                                {issue.priority}
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
                {issues && issues.length > 0
                  ? "No issues match the current filters."
                  : "No issues found. Create one to get started!"}
              </p>
              {hasActiveFilters && issues && issues.length > 0 && (
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

      <CreateIssueDialog
        open={createDialogOpen}
        onOpenChange={setCreateDialogOpen}
      />
    </PageLayout>
  );
}
