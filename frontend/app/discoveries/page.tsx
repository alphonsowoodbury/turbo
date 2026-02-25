"use client";

import { useState, useMemo } from "react";
import Link from "next/link";
import { PageLayout } from "@/components/layout/page-layout";
import { useIssues } from "@/hooks/use-issues";
import { useProjects } from "@/hooks/use-projects";
import { CreateIssueDialog } from "@/components/issues/create-issue-dialog";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Filter, X, Plus } from "lucide-react";
import { cn } from "@/lib/utils";
import { formatDistanceToNow } from "date-fns";
import { SubagentButton } from "@/components/subagent/subagent-button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

const priorityColors: Record<string, string> = {
  low: "bg-blue-500/10 text-blue-500 hover:bg-blue-500/20",
  medium: "bg-yellow-500/10 text-yellow-500 hover:bg-yellow-500/20",
  high: "bg-orange-500/10 text-orange-500 hover:bg-orange-500/20",
  critical: "bg-red-500/10 text-red-500 hover:bg-red-500/20",
};

const discoveryStatusColors: Record<string, string> = {
  proposed: "bg-purple-500/10 text-purple-500 hover:bg-purple-500/20",
  researching: "bg-indigo-500/10 text-indigo-500 hover:bg-indigo-500/20",
  findings_ready: "bg-violet-500/10 text-violet-500 hover:bg-violet-500/20",
  approved: "bg-green-500/10 text-green-500 hover:bg-green-500/20",
  parked: "bg-yellow-500/10 text-yellow-500 hover:bg-yellow-500/20",
  declined: "bg-gray-500/10 text-gray-500 hover:bg-gray-500/20",
};

export default function DiscoveriesPage() {
  const [createDialogOpen, setCreateDialogOpen] = useState(false);
  const [showFilters, setShowFilters] = useState(false);
  const [selectedProject, setSelectedProject] = useState<string>("all");
  const [selectedStatus, setSelectedStatus] = useState<string>("all");
  const [selectedPriority, setSelectedPriority] = useState<string>("all");
  const [groupBy, setGroupBy] = useState<string>("none");

  const { data: allIssues, isLoading, error } = useIssues();
  const { data: projects } = useProjects();

  // Filter to only discovery issues
  const discoveryIssues = useMemo(() => {
    if (!allIssues) return [];
    return allIssues.filter((issue) => issue.type === "discovery");
  }, [allIssues]);

  // Apply filters
  const filteredDiscoveries = useMemo(() => {
    let filtered = discoveryIssues;

    if (selectedProject !== "all") {
      if (selectedProject === "none") {
        // Filter for discoveries without a project
        filtered = filtered.filter((d) => !d.project_id);
      } else {
        filtered = filtered.filter((d) => d.project_id === selectedProject);
      }
    }

    if (selectedStatus !== "all") {
      filtered = filtered.filter((d) => (d.discovery_status || "proposed") === selectedStatus);
    }

    if (selectedPriority !== "all") {
      filtered = filtered.filter((d) => d.priority === selectedPriority);
    }

    return filtered;
  }, [discoveryIssues, selectedProject, selectedStatus, selectedPriority]);

  // Group discoveries
  const groupedDiscoveries = useMemo(() => {
    if (groupBy === "none") {
      return { "All Discoveries": filteredDiscoveries };
    }

    const groups: Record<string, typeof filteredDiscoveries> = {};

    filteredDiscoveries.forEach((discovery) => {
      let key = "";

      if (groupBy === "project") {
        if (!discovery.project_id) {
          key = "No Project";
        } else {
          const project = projects?.find((p) => p.id === discovery.project_id);
          key = project?.name || "Unknown Project";
        }
      } else if (groupBy === "status") {
        key = (discovery.discovery_status || "proposed").replace("_", " ");
      } else if (groupBy === "priority") {
        key = discovery.priority;
      }

      if (!groups[key]) {
        groups[key] = [];
      }
      groups[key].push(discovery);
    });

    return groups;
  }, [filteredDiscoveries, groupBy, projects]);

  const hasActiveFilters = selectedProject !== "all" || selectedStatus !== "all" || selectedPriority !== "all";

  const clearFilters = () => {
    setSelectedProject("all");
    setSelectedStatus("all");
    setSelectedPriority("all");
  };

  return (
    <PageLayout title="Discovery" isLoading={isLoading} error={error}>
      <div className="flex-1 p-6">
        {/* Controls Bar */}
        <div className="mb-4 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Button onClick={() => setCreateDialogOpen(true)}>
              <Plus className="h-4 w-4 mr-2" />
              New Discovery
            </Button>
            <SubagentButton
              suggestedAgent="discovery-guide"
              suggestedPrompt="Help me analyze my discovery issues and decide next steps for research topics."
              size="default"
            />
          </div>
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
                  {[selectedProject !== "all", selectedStatus !== "all", selectedPriority !== "all"].filter(Boolean).length}
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
                <SelectItem value="priority">Priority</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </div>

        {/* Filter Controls */}
        {showFilters && (
          <Card className="mb-4">
            <CardContent className="pt-6">
              <div className="grid grid-cols-3 gap-4">
                <div className="space-y-2">
                  <label className="text-sm font-medium">Project</label>
                  <Select value={selectedProject} onValueChange={setSelectedProject}>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="all">All Projects</SelectItem>
                      <SelectItem value="none">No Project</SelectItem>
                      {projects?.map((project) => (
                        <SelectItem key={project.id} value={project.id}>
                          {project.name}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>

                <div className="space-y-2">
                  <label className="text-sm font-medium">Discovery Status</label>
                  <Select value={selectedStatus} onValueChange={setSelectedStatus}>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="all">All Statuses</SelectItem>
                      <SelectItem value="proposed">Proposed</SelectItem>
                      <SelectItem value="researching">Researching</SelectItem>
                      <SelectItem value="findings_ready">Findings Ready</SelectItem>
                      <SelectItem value="approved">Approved</SelectItem>
                      <SelectItem value="parked">Parked</SelectItem>
                      <SelectItem value="declined">Declined</SelectItem>
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
              </div>
            </CardContent>
          </Card>
        )}

        {/* Results */}
        {filteredDiscoveries.length > 0 ? (
          <div className="space-y-6">
            {Object.entries(groupedDiscoveries).map(([groupName, discoveries]) => (
              <div key={groupName}>
                {groupBy !== "none" && (
                  <h3 className="mb-3 text-sm font-semibold text-muted-foreground capitalize">
                    {groupName} ({discoveries.length})
                  </h3>
                )}
                <div className="space-y-3">
                  {discoveries.map((discovery) => {
                    const project = projects?.find((p) => p.id === discovery.project_id);
                    const discoveryStatus = discovery.discovery_status || "proposed";

                    return (
                      <Link key={discovery.id} href={`/issues/${discovery.id}`}>
                        <Card className="hover:border-primary/50 cursor-pointer transition-colors">
                          <CardContent className="pt-6">
                            <div className="flex items-start justify-between gap-4">
                              <div className="flex-1 space-y-1">
                                <h3 className="font-semibold">{discovery.title}</h3>
                                <p className="text-sm text-muted-foreground line-clamp-2">
                                  {discovery.description}
                                </p>
                                <div className="flex items-center gap-2 text-xs text-muted-foreground">
                                  {project && (
                                    <>
                                      <span>{project.name}</span>
                                      <span>•</span>
                                    </>
                                  )}
                                  <span>
                                    Updated {formatDistanceToNow(new Date(discovery.updated_at))}{" "}
                                    ago
                                  </span>
                                  {discovery.assignee && (
                                    <>
                                      <span>•</span>
                                      <span>Assigned to {discovery.assignee}</span>
                                    </>
                                  )}
                                </div>
                              </div>
                              <div className="flex gap-2">
                                <Badge
                                  variant="secondary"
                                  className={cn(
                                    "text-xs capitalize",
                                    discoveryStatusColors[discoveryStatus]
                                  )}
                                >
                                  {discoveryStatus.replace("_", " ")}
                                </Badge>
                                <Badge
                                  variant="secondary"
                                  className={cn("text-xs", priorityColors[discovery.priority])}
                                >
                                  {discovery.priority}
                                </Badge>
                              </div>
                            </div>
                          </CardContent>
                        </Card>
                      </Link>
                    );
                  })}
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="flex h-64 items-center justify-center">
            <div className="text-center">
              <p className="text-sm text-muted-foreground">
                {discoveryIssues.length === 0
                  ? "No discoveries found. Create one to get started!"
                  : "No discoveries match the current filters."}
              </p>
              {hasActiveFilters && discoveryIssues.length > 0 && (
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
        defaultType="discovery"
      />
    </PageLayout>
  );
}
