"use client";

import { useState, useMemo } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { PageLayout } from "@/components/layout/page-layout";
import { useProject } from "@/hooks/use-projects";
import { useIssues } from "@/hooks/use-issues";
import { CreateIssueDialog } from "@/components/issues/create-issue-dialog";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Save, Trash2, Plus, Filter, X } from "lucide-react";
import { cn } from "@/lib/utils";
import { formatDistanceToNow } from "date-fns";
import { IssueFiltersComponent, type IssueFilters as IssueFiltersType } from "@/components/projects/issue-filters";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { useSavedFilters, useCreateSavedFilter, useDeleteSavedFilter } from "@/hooks/use-saved-filters";
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
} from "@/components/ui/dropdown-menu";

const priorityColors: Record<string, string> = {
  low: "bg-blue-500/10 text-blue-500 hover:bg-blue-500/20",
  medium: "bg-yellow-500/10 text-yellow-500 hover:bg-yellow-500/20",
  high: "bg-orange-500/10 text-orange-500 hover:bg-orange-500/20",
  critical: "bg-red-500/10 text-red-500 hover:bg-red-500/20",
};

export default function ProjectIssuesPage() {
  const params = useParams();
  const projectId = params.id as string;
  const [createIssueOpen, setCreateIssueOpen] = useState(false);
  const [filters, setFilters] = useState<IssueFiltersType>({});
  const [saveFilterOpen, setSaveFilterOpen] = useState(false);
  const [showFilters, setShowFilters] = useState(false);
  const [filterName, setFilterName] = useState("");
  const [filterDescription, setFilterDescription] = useState("");
  const [groupBy, setGroupBy] = useState<string>("none");
  const [sortBy, setSortBy] = useState<string>("updated");

  const { data: project, isLoading, error } = useProject(projectId);
  const { data: issues } = useIssues({ project_id: projectId });
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

  // Sort issues
  const sortedIssues = useMemo(() => {
    const sorted = [...filteredIssues];

    switch (sortBy) {
      case "updated":
        return sorted.sort((a, b) => new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime());
      case "created":
        return sorted.sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime());
      case "priority":
        const priorityOrder: Record<string, number> = { critical: 0, high: 1, medium: 2, low: 3 };
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

      if (groupBy === "status") {
        key = issue.status.replace("_", " ");
      } else if (groupBy === "priority") {
        key = issue.priority;
      } else if (groupBy === "type") {
        key = issue.type;
      }

      if (!groups[key]) {
        groups[key] = [];
      }
      groups[key].push(issue);
    });

    return groups;
  }, [sortedIssues, groupBy]);

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

  return (
    <PageLayout
      title="Issues"
      isLoading={isLoading}
      error={error || (!project ? new Error("Project not found") : null)}
      breadcrumbs={[
        { label: project?.name || "Project", href: `/projects/${projectId}` },
      ]}
    >
      <div className="space-y-6 p-6">

        {/* Issues Card */}
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <CardTitle>Issues</CardTitle>
                <Badge variant="secondary" className="h-5 px-2 text-xs">
                  {filteredIssues.length}
                  {filteredIssues.length !== issues?.length && ` / ${issues?.length}`}
                </Badge>
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
                <span className="text-sm text-muted-foreground self-center">Sort:</span>
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
                <span className="text-sm text-muted-foreground self-center">Group:</span>
                <Select value={groupBy} onValueChange={setGroupBy}>
                  <SelectTrigger className="w-32 h-8">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="none">None</SelectItem>
                    <SelectItem value="status">Status</SelectItem>
                    <SelectItem value="priority">Priority</SelectItem>
                    <SelectItem value="type">Type</SelectItem>
                  </SelectContent>
                </Select>
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
              <div className="space-y-6">
                {Object.entries(groupedIssues).map(([groupName, groupIssues]) => (
                  <div key={groupName}>
                    {groupBy !== "none" && (
                      <h3 className="mb-3 text-sm font-semibold text-muted-foreground capitalize">
                        {groupName} ({groupIssues.length})
                      </h3>
                    )}
                    <div className="space-y-2">
                      {groupIssues.map((issue) => (
                        <Link key={issue.id} href={`/issues/${issue.id}`}>
                          <div className="flex items-center justify-between rounded-lg border p-3 hover:bg-muted/50 cursor-pointer transition-colors">
                            <div className="flex-1">
                              <p className="font-medium">{issue.title}</p>
                              <p className="text-xs text-muted-foreground line-clamp-1">
                                {issue.description}
                              </p>
                              <p className="text-xs text-muted-foreground mt-1">
                                Updated {formatDistanceToNow(new Date(issue.updated_at))} ago
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
                  </div>
                ))}
              </div>
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

      <CreateIssueDialog
        open={createIssueOpen}
        onOpenChange={setCreateIssueOpen}
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