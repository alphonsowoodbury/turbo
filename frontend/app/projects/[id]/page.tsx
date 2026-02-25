"use client";

import { useState, useMemo } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { PageLayout } from "@/components/layout/page-layout";
import { useProject } from "@/hooks/use-projects";
import { useIssues } from "@/hooks/use-issues";
import { useMilestones } from "@/hooks/use-milestones";
import { useInitiatives } from "@/hooks/use-initiatives";
import { CreateIssueDialog } from "@/components/issues/create-issue-dialog";
import { CreateMilestoneDialog } from "@/components/milestones/create-milestone-dialog";
import { EntityCommentsSection } from "@/components/shared/entity-comments-section";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Save, Trash2, Plus, Filter, ExternalLink, Calendar } from "lucide-react";
import { cn } from "@/lib/utils";
import { formatDistanceToNow, format } from "date-fns";
import { IssueFiltersComponent, type IssueFilters as IssueFiltersType } from "@/components/projects/issue-filters";
import { ActivityFeed } from "@/components/projects/activity-feed";
import { useSavedFilters, useCreateSavedFilter, useDeleteSavedFilter } from "@/hooks/use-saved-filters";
import { SubagentButton } from "@/components/subagent/subagent-button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
  DropdownMenuSeparator,
} from "@/components/ui/dropdown-menu";

const priorityColors: Record<string, string> = {
  low: "bg-blue-500/10 text-blue-500 hover:bg-blue-500/20",
  medium: "bg-yellow-500/10 text-yellow-500 hover:bg-yellow-500/20",
  high: "bg-orange-500/10 text-orange-500 hover:bg-orange-500/20",
  critical: "bg-red-500/10 text-red-500 hover:bg-red-500/20",
};

const statusColors: Record<string, string> = {
  active: "bg-green-500/10 text-green-500 hover:bg-green-500/20",
  on_hold: "bg-yellow-500/10 text-yellow-500 hover:bg-yellow-500/20",
  completed: "bg-blue-500/10 text-blue-500 hover:bg-blue-500/20",
  archived: "bg-gray-500/10 text-gray-500 hover:bg-gray-500/20",
};

const milestoneStatusColors: Record<string, string> = {
  planned: "bg-gray-500/10 text-gray-500 hover:bg-gray-500/20",
  in_progress: "bg-blue-500/10 text-blue-500 hover:bg-blue-500/20",
  completed: "bg-green-500/10 text-green-500 hover:bg-green-500/20",
  cancelled: "bg-red-500/10 text-red-500 hover:bg-red-500/20",
};

const initiativeStatusColors: Record<string, string> = {
  planning: "bg-gray-500/10 text-gray-500 hover:bg-gray-500/20",
  in_progress: "bg-blue-500/10 text-blue-500 hover:bg-blue-500/20",
  on_hold: "bg-yellow-500/10 text-yellow-500 hover:bg-yellow-500/20",
  completed: "bg-green-500/10 text-green-500 hover:bg-green-500/20",
  cancelled: "bg-red-500/10 text-red-500 hover:bg-red-500/20",
};

export default function ProjectDetailPage() {
  const params = useParams();
  const projectId = params.id as string;
  const [createIssueOpen, setCreateIssueOpen] = useState(false);
  const [createMilestoneOpen, setCreateMilestoneOpen] = useState(false);
  const [filters, setFilters] = useState<IssueFiltersType>({});
  const [saveFilterOpen, setSaveFilterOpen] = useState(false);
  const [showFilters, setShowFilters] = useState(false);
  const [filterName, setFilterName] = useState("");
  const [filterDescription, setFilterDescription] = useState("");

  const { data: project, isLoading, error } = useProject(projectId);
  const { data: issues } = useIssues({ project_id: projectId });
  const { data: milestones } = useMilestones({ project_id: projectId });
  const { data: initiatives } = useInitiatives({ project_id: projectId });
  const { data: savedFilters } = useSavedFilters(projectId);
  const createFilter = useCreateSavedFilter();
  const deleteFilter = useDeleteSavedFilter();

  // Filter issues based on active filters
  const filteredIssues = useMemo(() => {
    if (!issues) return [];

    return issues.filter((issue) => {
      if (filters.search && !issue.title.toLowerCase().includes(filters.search.toLowerCase()) &&
          !issue.description?.toLowerCase().includes(filters.search.toLowerCase())) {
        return false;
      }
      if (filters.status && issue.status !== filters.status) {
        return false;
      }
      if (filters.priority && issue.priority !== filters.priority) {
        return false;
      }
      if (filters.type && issue.issue_type !== filters.type) {
        return false;
      }
      return true;
    });
  }, [issues, filters]);

  const handleSaveFilter = async () => {
    if (!filterName.trim()) return;

    await createFilter.mutateAsync({
      name: filterName,
      description: filterDescription,
      filter_config: JSON.stringify(filters),
      project_id: projectId,
    });

    setFilterName("");
    setFilterDescription("");
    setSaveFilterOpen(false);
  };

  const handleLoadFilter = (filterConfig: string) => {
    try {
      const parsedFilters = JSON.parse(filterConfig);
      setFilters(parsedFilters);
    } catch (e) {
      console.error("Failed to parse filter config:", e);
    }
  };

  // Early return if no project data
  if (!project) {
    return (
      <PageLayout
        title="Project Not Found"
        isLoading={isLoading}
        error={error || new Error("Project not found")}
      >
        <div />
      </PageLayout>
    );
  }

  return (
    <PageLayout
      title={project.name}
      isLoading={isLoading}
      error={error}
    >
      <div className="flex flex-col h-full overflow-hidden">
        {/* Scrollable Content Area */}
        <div className="flex-1 overflow-y-auto space-y-6 p-6 pb-0">
        {/* Project Info with Tabs */}
        <Card>
          <CardHeader>
            <div className="flex items-start justify-between">
              <div className="space-y-2">
                <CardTitle>{project.name}</CardTitle>
                <p className="text-sm text-muted-foreground">
                  {project.description}
                </p>
              </div>
              <div className="flex gap-2 items-center">
                <SubagentButton
                  context={{ project_id: projectId }}
                  suggestedAgent="project-manager"
                  suggestedPrompt="Generate a comprehensive health report for this project including status, risks, and recommendations."
                  size="sm"
                />
                <Badge
                  variant="secondary"
                  className={cn("text-xs", priorityColors[project.priority])}
                >
                  {project.priority}
                </Badge>
                <Badge
                  variant="secondary"
                  className={cn(
                    "text-xs capitalize",
                    statusColors[project.status]
                  )}
                >
                  {project.status.replace("_", " ")}
                </Badge>
              </div>
            </div>

            {/* Metadata */}
            <div className="grid gap-4 text-sm md:grid-cols-2 mt-4">
              <div>
                <span className="text-muted-foreground">Created: </span>
                <span>
                  {formatDistanceToNow(new Date(project.created_at))} ago
                </span>
              </div>
              <div>
                <span className="text-muted-foreground">Updated: </span>
                <span>
                  {formatDistanceToNow(new Date(project.updated_at))} ago
                </span>
              </div>
            </div>
          </CardHeader>
          <CardContent>
            <Tabs defaultValue="strategy" className="w-full">
              <TabsList className="grid w-full grid-cols-6">
                <TabsTrigger value="strategy">Strategy</TabsTrigger>
                <TabsTrigger value="stack">Tech Stack</TabsTrigger>
                <TabsTrigger value="documents">Documents</TabsTrigger>
                <TabsTrigger value="blueprints">Blueprints</TabsTrigger>
                <TabsTrigger value="marketing">Marketing</TabsTrigger>
                <TabsTrigger value="activity">Activity</TabsTrigger>
              </TabsList>

              <TabsContent value="strategy" className="space-y-6 mt-6">
                <div className="text-center py-12">
                  <p className="text-sm text-muted-foreground">
                    Strategy content coming soon...
                  </p>
                </div>
              </TabsContent>

              <TabsContent value="stack" className="space-y-6 mt-6">
                <div className="text-center py-12">
                  <p className="text-sm text-muted-foreground">
                    Tech Stack content coming soon...
                  </p>
                </div>
              </TabsContent>

              <TabsContent value="documents" className="space-y-6 mt-6">
                <div className="text-center py-12">
                  <p className="text-sm text-muted-foreground">
                    Documents content coming soon...
                  </p>
                </div>
              </TabsContent>

              <TabsContent value="blueprints" className="space-y-6 mt-6">
                <div className="text-center py-12">
                  <p className="text-sm text-muted-foreground">
                    Blueprints content coming soon...
                  </p>
                </div>
              </TabsContent>

              <TabsContent value="marketing" className="space-y-6 mt-6">
                <div className="text-center py-12">
                  <p className="text-sm text-muted-foreground">
                    Marketing content coming soon...
                  </p>
                </div>
              </TabsContent>

              <TabsContent value="activity" className="space-y-6 mt-6">
                <ActivityFeed projectId={projectId} />
              </TabsContent>
            </Tabs>
          </CardContent>
        </Card>

        {/* Milestones */}
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <CardTitle>Milestones</CardTitle>
                <Badge variant="secondary" className="h-5 px-2 text-xs">
                  {milestones?.length || 0}
                </Badge>
                <Link href={`/milestones?project_id=${projectId}`}>
                  <Button variant="ghost" size="sm" className="h-6 w-6 p-0">
                    <ExternalLink className="h-3 w-3" />
                  </Button>
                </Link>
              </div>
              <Button
                size="sm"
                onClick={() => setCreateMilestoneOpen(true)}
                className="h-8"
              >
                <Plus className="h-4 w-4 mr-1" />
                New Milestone
              </Button>
            </div>
          </CardHeader>
          <CardContent>
            {milestones && milestones.length > 0 ? (
              <div className="space-y-2">
                {milestones.slice(0, 5).map((milestone) => (
                  <Link key={milestone.id} href={`/milestones/${milestone.id}`}>
                    <div className="flex items-center justify-between rounded-lg border p-3 hover:bg-muted/50 cursor-pointer transition-colors">
                      <div className="flex-1">
                        <p className="font-medium">{milestone.name}</p>
                        <div className="flex items-center gap-2 mt-1">
                          <Calendar className="h-3 w-3 text-muted-foreground" />
                          <p className="text-xs text-muted-foreground">
                            Due {format(new Date(milestone.due_date), "MMM d, yyyy")}
                          </p>
                          {milestone.issue_count > 0 && (
                            <>
                              <span className="text-muted-foreground">•</span>
                              <p className="text-xs text-muted-foreground">
                                {milestone.issue_count} {milestone.issue_count === 1 ? "issue" : "issues"}
                              </p>
                            </>
                          )}
                        </div>
                      </div>
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
                  </Link>
                ))}
              </div>
            ) : (
              <p className="text-sm text-muted-foreground">
                No milestones yet. Create one to track project goals.
              </p>
            )}
          </CardContent>
        </Card>

        {/* Initiatives */}
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <CardTitle>Initiatives</CardTitle>
                <Badge variant="secondary" className="h-5 px-2 text-xs">
                  {initiatives?.length || 0}
                </Badge>
                <Link href={`/initiatives?project_id=${projectId}`}>
                  <Button variant="ghost" size="sm" className="h-6 w-6 p-0">
                    <ExternalLink className="h-3 w-3" />
                  </Button>
                </Link>
              </div>
            </div>
          </CardHeader>
          <CardContent>
            {initiatives && initiatives.length > 0 ? (
              <div className="space-y-2">
                {initiatives.slice(0, 5).map((initiative) => (
                  <Link key={initiative.id} href={`/initiatives/${initiative.id}`}>
                    <div className="flex items-center justify-between rounded-lg border p-3 hover:bg-muted/50 cursor-pointer transition-colors">
                      <div className="flex-1">
                        <p className="font-medium">{initiative.name}</p>
                        <p className="text-xs text-muted-foreground line-clamp-1 mt-1">
                          {initiative.description}
                        </p>
                        <div className="flex items-center gap-2 mt-1">
                          {initiative.issue_count > 0 && (
                            <p className="text-xs text-muted-foreground">
                              {initiative.issue_count} {initiative.issue_count === 1 ? "issue" : "issues"}
                            </p>
                          )}
                        </div>
                      </div>
                      <Badge
                        variant="secondary"
                        className={cn(
                          "text-xs capitalize",
                          initiativeStatusColors[initiative.status]
                        )}
                      >
                        {initiative.status.replace("_", " ")}
                      </Badge>
                    </div>
                  </Link>
                ))}
              </div>
            ) : (
              <p className="text-sm text-muted-foreground">
                No initiatives yet. Create one to organize work by feature or technology.
              </p>
            )}
          </CardContent>
        </Card>

        {/* Issues */}
        <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <CardTitle>Issues</CardTitle>
                  <Badge variant="secondary" className="h-5 px-2 text-xs">
                    {filteredIssues.length}
                    {filteredIssues.length !== issues?.length && ` / ${issues?.length}`}
                  </Badge>
                  <Link href={`/projects/${projectId}/issues`}>
                    <Button variant="ghost" size="sm" className="h-6 w-6 p-0">
                      <ExternalLink className="h-3 w-3" />
                    </Button>
                  </Link>
                </div>
                <div className="flex gap-2">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setShowFilters(!showFilters)}
                    className="h-8"
                  >
                    <Filter className="h-4 w-4 mr-1" />
                    Filter
                  </Button>
                  {savedFilters && savedFilters.length > 0 && (
                    <DropdownMenu>
                      <DropdownMenuTrigger asChild>
                        <Button variant="outline" size="sm" className="h-8">
                          Saved
                        </Button>
                      </DropdownMenuTrigger>
                      <DropdownMenuContent align="end" className="w-56">
                        {savedFilters.map((filter) => (
                          <DropdownMenuItem
                            key={filter.id}
                            className="flex items-center justify-between"
                            onClick={() => handleLoadFilter(filter.filter_config)}
                          >
                            <span className="truncate flex-1">{filter.name}</span>
                            <Button
                              variant="ghost"
                              size="sm"
                              className="h-6 w-6 p-0 ml-2"
                              onClick={(e) => {
                                e.stopPropagation();
                                deleteFilter.mutate(filter.id);
                              }}
                            >
                              <Trash2 className="h-3 w-3" />
                            </Button>
                          </DropdownMenuItem>
                        ))}
                      </DropdownMenuContent>
                    </DropdownMenu>
                  )}
                  <Button
                    size="sm"
                    onClick={() => setCreateIssueOpen(true)}
                    className="h-8"
                  >
                    <Plus className="h-4 w-4 mr-1" />
                    New Issue
                  </Button>
                </div>
              </div>
            </CardHeader>
            <CardContent>
              {showFilters && (
                <div className="mb-4 pb-4 border-b">
                  <IssueFiltersComponent
                    filters={filters}
                    onFiltersChange={setFilters}
                    onSaveClick={() => setSaveFilterOpen(true)}
                  />
                </div>
              )}

              {filteredIssues.length > 0 ? (
                <>
                  <div className="space-y-2">
                    {filteredIssues.slice(0, 10).map((issue) => (
                      <Link key={issue.id} href={`/issues/${issue.id}`}>
                        <div className="flex items-center justify-between rounded-lg border p-3 hover:bg-muted/50 cursor-pointer transition-colors">
                          <div className="flex-1">
                            <p className="font-medium">{issue.title}</p>
                            <p className="text-xs text-muted-foreground line-clamp-1">
                              {issue.description}
                            </p>
                          </div>
                          <div className="flex gap-2">
                            <Badge variant="outline" className="text-xs capitalize">
                              {issue.status.replace("_", " ")}
                            </Badge>
                            <Badge
                              variant="secondary"
                              className={cn(
                                "text-xs",
                                priorityColors[issue.priority]
                              )}
                            >
                              {issue.priority}
                            </Badge>
                          </div>
                        </div>
                      </Link>
                    ))}
                  </div>
                </>
              ) : (
                <p className="text-sm text-muted-foreground">
                  {issues && issues.length > 0
                    ? "No issues match the current filters."
                    : "No issues yet. Create one to get started."}
                </p>
              )}
            </CardContent>
        </Card>
        </div>

        {/* Collapsible & Resizable Comments Section */}
        <EntityCommentsSection
          entityType="project"
          entityId={projectId}
          defaultHeight={500}
          minHeight={200}
          maxHeight={800}
          title="Comments"
        />
      </div>

      <CreateIssueDialog
        open={createIssueOpen}
        onOpenChange={setCreateIssueOpen}
        projectId={projectId}
      />

      <CreateMilestoneDialog
        open={createMilestoneOpen}
        onOpenChange={setCreateMilestoneOpen}
        projectId={projectId}
      />

      <Dialog open={saveFilterOpen} onOpenChange={setSaveFilterOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Save Filter</DialogTitle>
            <DialogDescription>
              Save your current filters for quick access later.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="filter-name">Filter Name</Label>
              <Input
                id="filter-name"
                placeholder="e.g., High Priority Bugs"
                value={filterName}
                onChange={(e) => setFilterName(e.target.value)}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="filter-description">Description (optional)</Label>
              <Textarea
                id="filter-description"
                placeholder="What does this filter show?"
                value={filterDescription}
                onChange={(e) => setFilterDescription(e.target.value)}
                rows={3}
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setSaveFilterOpen(false)}>
              Cancel
            </Button>
            <Button onClick={handleSaveFilter} disabled={!filterName.trim()}>
              <Save className="h-4 w-4 mr-2" />
              Save Filter
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </PageLayout>
  );
}
