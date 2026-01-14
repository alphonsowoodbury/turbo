/**
 * CANONICAL PAGE TEMPLATE
 *
 * This is the official template for creating new entity list pages.
 * All new pages should follow this exact structure.
 *
 * Features:
 * - Milestones-style header using Header component
 * - Issues-style filter bar with full controls
 * - Loading and error states
 * - Empty states
 * - Filter, sort, and group functionality
 * - Card-based list view
 *
 * To create a new page:
 * 1. Copy this file
 * 2. Replace "Entity" with your entity name throughout
 * 3. Update the imports to match your entity
 * 4. Adjust filters and fields as needed for your entity
 * 5. Update color mappings for badges
 */

"use client";

import { useState, useMemo } from "react";
import Link from "next/link";
import { PageLayout } from "@/components/layout/page-layout";
// import { useEntities } from "@/hooks/use-entities";  // Replace with your hook
// import { useProjects } from "@/hooks/use-projects";  // If needed for filtering
// import { CreateEntityDialog } from "@/components/entities/create-entity-dialog";  // Replace with your dialog
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

// Define your color mappings for badges
const statusColors = {
  open: "bg-green-500/10 text-green-500 hover:bg-green-500/20",
  in_progress: "bg-blue-500/10 text-blue-500 hover:bg-blue-500/20",
  review: "bg-purple-500/10 text-purple-500 hover:bg-purple-500/20",
  completed: "bg-gray-500/10 text-gray-500 hover:bg-gray-500/20",
};

const priorityColors = {
  low: "bg-blue-500/10 text-blue-500 hover:bg-blue-500/20",
  medium: "bg-yellow-500/10 text-yellow-500 hover:bg-yellow-500/20",
  high: "bg-orange-500/10 text-orange-500 hover:bg-orange-500/20",
  critical: "bg-red-500/10 text-red-500 hover:bg-red-500/20",
};

export default function EntitiesPage() {
  // Dialog state
  const [createDialogOpen, setCreateDialogOpen] = useState(false);

  // Filter state
  const [showFilters, setShowFilters] = useState(false);
  const [selectedProject, setSelectedProject] = useState<string>("all");
  const [selectedStatus, setSelectedStatus] = useState<string>("all");
  const [selectedPriority, setSelectedPriority] = useState<string>("all");
  const [selectedCategory, setSelectedCategory] = useState<string>("all");  // Adjust as needed

  // Sort and group state
  const [groupBy, setGroupBy] = useState<string>("none");
  const [sortBy, setSortBy] = useState<string>("updated");

  // Data fetching - REPLACE THESE WITH YOUR ACTUAL HOOKS
  // const { data: entities, isLoading, error } = useEntities();
  // const { data: projects } = useProjects();

  // TEMPORARY - Remove when you have real hooks
  const entities: any[] = [];
  const projects: any[] = [];
  const isLoading = false;
  const error = null;

  // Apply filters
  const filteredEntities = useMemo(() => {
    if (!entities) return [];

    let filtered = entities;

    if (selectedProject !== "all") {
      filtered = filtered.filter((e: any) => e.project_id === selectedProject);
    }

    if (selectedStatus !== "all") {
      filtered = filtered.filter((e: any) => e.status === selectedStatus);
    }

    if (selectedPriority !== "all") {
      filtered = filtered.filter((e: any) => e.priority === selectedPriority);
    }

    if (selectedCategory !== "all") {
      filtered = filtered.filter((e: any) => e.category === selectedCategory);
    }

    return filtered;
  }, [entities, selectedProject, selectedStatus, selectedPriority, selectedCategory]);

  // Sort entities
  const sortedEntities = useMemo(() => {
    const sorted = [...filteredEntities];

    switch (sortBy) {
      case "updated":
        return sorted.sort((a: any, b: any) =>
          new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime()
        );
      case "created":
        return sorted.sort((a: any, b: any) =>
          new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
        );
      case "priority":
        const priorityOrder = { critical: 0, high: 1, medium: 2, low: 3 };
        return sorted.sort((a: any, b: any) =>
          priorityOrder[a.priority as keyof typeof priorityOrder] -
          priorityOrder[b.priority as keyof typeof priorityOrder]
        );
      case "name":
        return sorted.sort((a: any, b: any) => a.name.localeCompare(b.name));
      default:
        return sorted;
    }
  }, [filteredEntities, sortBy]);

  // Group entities
  const groupedEntities = useMemo(() => {
    if (groupBy === "none") {
      return { "All Entities": sortedEntities };
    }

    const groups: Record<string, typeof sortedEntities> = {};

    sortedEntities.forEach((entity: any) => {
      let key = "";

      if (groupBy === "project") {
        const project = projects?.find((p: any) => p.id === entity.project_id);
        key = project?.name || "Unknown Project";
      } else if (groupBy === "status") {
        key = entity.status.replace("_", " ");
      } else if (groupBy === "priority") {
        key = entity.priority;
      } else if (groupBy === "category") {
        key = entity.category;
      }

      if (!groups[key]) {
        groups[key] = [];
      }
      groups[key].push(entity);
    });

    return groups;
  }, [sortedEntities, groupBy, projects]);

  // Check for active filters
  const hasActiveFilters =
    selectedProject !== "all" ||
    selectedStatus !== "all" ||
    selectedPriority !== "all" ||
    selectedCategory !== "all";

  const clearFilters = () => {
    setSelectedProject("all");
    setSelectedStatus("all");
    setSelectedPriority("all");
    setSelectedCategory("all");
  };

  return (
    <PageLayout
      title="Entities"
      isLoading={isLoading}
      error={error}
    >
      <div className="p-6">
        {/* Controls Bar - Issues style */}
        <div className="mb-4 flex items-center justify-between">
          {/* Create Button */}
          <Button onClick={() => setCreateDialogOpen(true)}>
            <Plus className="h-4 w-4 mr-2" />
            New Entity
          </Button>

          {/* Filter, Sort, and Group Controls */}
          <div className="flex items-center gap-2">
            {/* Filter Button */}
            <Button
              variant={showFilters ? "secondary" : "outline"}
              size="sm"
              onClick={() => setShowFilters(!showFilters)}
            >
              <Filter className="h-4 w-4 mr-2" />
              Filter
              {hasActiveFilters && (
                <Badge variant="secondary" className="ml-2 h-4 px-1 text-[10px]">
                  {[
                    selectedProject !== "all",
                    selectedStatus !== "all",
                    selectedPriority !== "all",
                    selectedCategory !== "all",
                  ].filter(Boolean).length}
                </Badge>
              )}
            </Button>

            {/* Clear Filters Button */}
            {hasActiveFilters && (
              <Button variant="ghost" size="sm" onClick={clearFilters}>
                <X className="h-4 w-4 mr-1" />
                Clear
              </Button>
            )}

            {/* Sort Control */}
            <span className="text-sm text-muted-foreground">Sort:</span>
            <Select value={sortBy} onValueChange={setSortBy}>
              <SelectTrigger className="w-32 h-8">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="updated">Updated</SelectItem>
                <SelectItem value="created">Created</SelectItem>
                <SelectItem value="priority">Priority</SelectItem>
                <SelectItem value="name">Name</SelectItem>
              </SelectContent>
            </Select>

            {/* Group Control */}
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
                <SelectItem value="category">Category</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </div>

        {/* Filter Panel - Collapsible */}
        {showFilters && (
          <Card className="mb-4">
            <CardContent className="pt-6">
              <div className="grid grid-cols-4 gap-4">
                {/* Project Filter */}
                <div className="space-y-2">
                  <label className="text-sm font-medium">Project</label>
                  <Select value={selectedProject} onValueChange={setSelectedProject}>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="all">All Projects</SelectItem>
                      {projects?.map((project: any) => (
                        <SelectItem key={project.id} value={project.id}>
                          {project.name}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>

                {/* Status Filter */}
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
                      <SelectItem value="completed">Completed</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                {/* Priority Filter */}
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

                {/* Category Filter - Adjust as needed */}
                <div className="space-y-2">
                  <label className="text-sm font-medium">Category</label>
                  <Select value={selectedCategory} onValueChange={setSelectedCategory}>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="all">All Categories</SelectItem>
                      <SelectItem value="category1">Category 1</SelectItem>
                      <SelectItem value="category2">Category 2</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Entity List */}
        {filteredEntities.length > 0 ? (
          <div className="space-y-6">
            {Object.entries(groupedEntities).map(([groupName, groupEntities]) => (
              <div key={groupName}>
                {/* Group Header */}
                {groupBy !== "none" && (
                  <h3 className="mb-3 text-sm font-semibold text-muted-foreground capitalize">
                    {groupName} ({groupEntities.length})
                  </h3>
                )}

                {/* Entity Cards */}
                <div className="space-y-3">
                  {groupEntities.map((entity: any) => (
                    <Link key={entity.id} href={`/entities/${entity.id}`}>
                      <Card className="hover:border-primary/50 cursor-pointer transition-colors">
                        <CardContent className="pt-6">
                          <div className="flex items-start justify-between gap-4">
                            {/* Entity Content */}
                            <div className="flex-1 space-y-1">
                              <h3 className="font-semibold">{entity.name || entity.title}</h3>
                              <p className="text-sm text-muted-foreground line-clamp-2">
                                {entity.description}
                              </p>
                              <div className="flex items-center gap-2 text-xs text-muted-foreground">
                                <span>
                                  Updated {formatDistanceToNow(new Date(entity.updated_at))}{" "}
                                  ago
                                </span>
                                {/* Add more metadata as needed */}
                              </div>
                            </div>

                            {/* Entity Badges */}
                            <div className="flex gap-2">
                              {/* Category Badge - if applicable */}
                              {entity.category && (
                                <Badge variant="outline" className="text-xs capitalize">
                                  {entity.category}
                                </Badge>
                              )}

                              {/* Status Badge */}
                              <Badge
                                variant="secondary"
                                className={cn(
                                  "text-xs capitalize",
                                  statusColors[entity.status as keyof typeof statusColors]
                                )}
                              >
                                {entity.status.replace("_", " ")}
                              </Badge>

                              {/* Priority Badge */}
                              <Badge
                                variant="secondary"
                                className={cn(
                                  "text-xs",
                                  priorityColors[entity.priority as keyof typeof priorityColors]
                                )}
                              >
                                {entity.priority}
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
          /* Empty State */
          <div className="flex h-64 items-center justify-center">
            <div className="text-center">
              <p className="text-sm text-muted-foreground">
                {entities && entities.length > 0
                  ? "No entities match the current filters."
                  : "No entities found. Create one to get started!"}
              </p>
              {hasActiveFilters && entities && entities.length > 0 && (
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

      {/* Create Dialog - Replace with your actual dialog */}
      {/* <CreateEntityDialog
        open={createDialogOpen}
        onOpenChange={setCreateDialogOpen}
      /> */}
    </PageLayout>
  );
}
