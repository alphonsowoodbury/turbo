"use client";

import { useState, useMemo } from "react";
import Link from "next/link";
import { PageLayout } from "@/components/layout/page-layout";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { TagBadge } from "@/components/tags";
import { Plus, Filter, X, Tags as TagsIcon } from "lucide-react";
import { cn } from "@/lib/utils";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

// Color categories for filtering
const colorCategories = {
  blue: "#3B82F6",
  green: "#10B981",
  red: "#EF4444",
  purple: "#8B5CF6",
  yellow: "#F59E0B",
  pink: "#EC4899",
  gray: "#6B7280",
  orange: "#F97316",
};

export default function TagsPage() {
  // Dialog state
  const [createDialogOpen, setCreateDialogOpen] = useState(false);

  // Filter state
  const [showFilters, setShowFilters] = useState(false);
  const [selectedColor, setSelectedColor] = useState<string>("all");
  const [selectedItemType, setSelectedItemType] = useState<string>("all");
  const [minUsageCount, setMinUsageCount] = useState<string>("all");

  // Sort and group state
  const [groupBy, setGroupBy] = useState<string>("none");
  const [sortBy, setSortBy] = useState<string>("name");

  // Mock data - will be replaced with API calls
  const tags = [
    {
      id: "1",
      name: "frontend",
      color: "#3B82F6",
      description: "Frontend development tasks",
      created_at: "2024-01-15T10:00:00Z",
      updated_at: "2024-03-20T14:30:00Z",
      usage: {
        total: 45,
        projects: 5,
        issues: 32,
        milestones: 4,
        initiatives: 2,
        literature: 2,
      }
    },
    {
      id: "2",
      name: "backend",
      color: "#10B981",
      description: "Backend development tasks",
      created_at: "2024-01-15T10:00:00Z",
      updated_at: "2024-03-18T11:15:00Z",
      usage: {
        total: 32,
        projects: 3,
        issues: 26,
        milestones: 2,
        initiatives: 1,
        literature: 0,
      }
    },
    {
      id: "3",
      name: "bug",
      color: "#EF4444",
      description: "Bug fixes and issues",
      created_at: "2024-01-15T10:00:00Z",
      updated_at: "2024-03-22T09:45:00Z",
      usage: {
        total: 18,
        projects: 0,
        issues: 18,
        milestones: 0,
        initiatives: 0,
        literature: 0,
      }
    },
    {
      id: "4",
      name: "feature",
      color: "#8B5CF6",
      description: "New feature development",
      created_at: "2024-01-15T10:00:00Z",
      updated_at: "2024-03-23T16:20:00Z",
      usage: {
        total: 67,
        projects: 8,
        issues: 45,
        milestones: 8,
        initiatives: 6,
        literature: 0,
      }
    },
    {
      id: "5",
      name: "urgent",
      color: "#F59E0B",
      description: "Time-sensitive tasks",
      created_at: "2024-01-15T10:00:00Z",
      updated_at: "2024-03-21T13:10:00Z",
      usage: {
        total: 12,
        projects: 2,
        issues: 10,
        milestones: 0,
        initiatives: 0,
        literature: 0,
      }
    },
    {
      id: "6",
      name: "design",
      color: "#EC4899",
      description: "Design and UX work",
      created_at: "2024-01-15T10:00:00Z",
      updated_at: "2024-03-19T08:30:00Z",
      usage: {
        total: 28,
        projects: 4,
        issues: 20,
        milestones: 3,
        initiatives: 1,
        literature: 0,
      }
    },
  ];

  const isLoading = false;
  const error = null;

  // Helper function to get color category
  const getColorCategory = (hexColor: string): string => {
    const entry = Object.entries(colorCategories).find(([_, hex]) =>
      hex.toLowerCase() === hexColor.toLowerCase()
    );
    return entry ? entry[0] : "other";
  };

  // Apply filters
  const filteredTags = useMemo(() => {
    if (!tags) return [];

    let filtered = tags;

    if (selectedColor !== "all") {
      filtered = filtered.filter((tag) =>
        getColorCategory(tag.color) === selectedColor
      );
    }

    if (selectedItemType !== "all") {
      filtered = filtered.filter((tag) => {
        const usage = tag.usage as any;
        return usage[selectedItemType] > 0;
      });
    }

    if (minUsageCount !== "all") {
      const minCount = parseInt(minUsageCount);
      filtered = filtered.filter((tag) => tag.usage.total >= minCount);
    }

    return filtered;
  }, [tags, selectedColor, selectedItemType, minUsageCount]);

  // Sort tags
  const sortedTags = useMemo(() => {
    const sorted = [...filteredTags];

    switch (sortBy) {
      case "name":
        return sorted.sort((a, b) => a.name.localeCompare(b.name));
      case "usage":
        return sorted.sort((a, b) => b.usage.total - a.usage.total);
      case "updated":
        return sorted.sort((a, b) =>
          new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime()
        );
      case "created":
        return sorted.sort((a, b) =>
          new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
        );
      default:
        return sorted;
    }
  }, [filteredTags, sortBy]);

  // Group tags
  const groupedTags = useMemo(() => {
    if (groupBy === "none") {
      return { "All Tags": sortedTags };
    }

    const groups: Record<string, typeof sortedTags> = {};

    sortedTags.forEach((tag) => {
      let key = "";

      if (groupBy === "color") {
        key = getColorCategory(tag.color);
      } else if (groupBy === "usage") {
        if (tag.usage.total >= 50) key = "High Usage (50+)";
        else if (tag.usage.total >= 20) key = "Medium Usage (20-49)";
        else if (tag.usage.total >= 10) key = "Low Usage (10-19)";
        else key = "Minimal Usage (< 10)";
      }

      if (!groups[key]) {
        groups[key] = [];
      }
      groups[key].push(tag);
    });

    return groups;
  }, [sortedTags, groupBy]);

  // Check for active filters
  const hasActiveFilters =
    selectedColor !== "all" ||
    selectedItemType !== "all" ||
    minUsageCount !== "all";

  const clearFilters = () => {
    setSelectedColor("all");
    setSelectedItemType("all");
    setMinUsageCount("all");
  };

  return (
    <PageLayout title="Tags" isLoading={isLoading} error={error}>
      <div className="p-6">
        {/* Controls Bar */}
        <div className="mb-4 flex items-center justify-between">
          {/* Create Button */}
          <Button onClick={() => setCreateDialogOpen(true)}>
            <Plus className="h-4 w-4 mr-2" />
            New Tag
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
                    selectedColor !== "all",
                    selectedItemType !== "all",
                    minUsageCount !== "all",
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
                <SelectItem value="name">Name</SelectItem>
                <SelectItem value="usage">Usage</SelectItem>
                <SelectItem value="updated">Updated</SelectItem>
                <SelectItem value="created">Created</SelectItem>
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
                <SelectItem value="color">Color</SelectItem>
                <SelectItem value="usage">Usage</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </div>

        {/* Filter Panel */}
        {showFilters && (
          <Card className="mb-4">
            <CardContent className="pt-6">
              <div className="grid grid-cols-3 gap-4">
                {/* Color Filter */}
                <div className="space-y-2">
                  <label className="text-sm font-medium">Color</label>
                  <Select value={selectedColor} onValueChange={setSelectedColor}>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="all">All Colors</SelectItem>
                      <SelectItem value="blue">Blue</SelectItem>
                      <SelectItem value="green">Green</SelectItem>
                      <SelectItem value="red">Red</SelectItem>
                      <SelectItem value="purple">Purple</SelectItem>
                      <SelectItem value="yellow">Yellow</SelectItem>
                      <SelectItem value="pink">Pink</SelectItem>
                      <SelectItem value="gray">Gray</SelectItem>
                      <SelectItem value="orange">Orange</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                {/* Item Type Filter */}
                <div className="space-y-2">
                  <label className="text-sm font-medium">Used In</label>
                  <Select value={selectedItemType} onValueChange={setSelectedItemType}>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="all">All Types</SelectItem>
                      <SelectItem value="projects">Projects</SelectItem>
                      <SelectItem value="issues">Issues</SelectItem>
                      <SelectItem value="milestones">Milestones</SelectItem>
                      <SelectItem value="initiatives">Initiatives</SelectItem>
                      <SelectItem value="literature">Literature</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                {/* Usage Count Filter */}
                <div className="space-y-2">
                  <label className="text-sm font-medium">Min Usage</label>
                  <Select value={minUsageCount} onValueChange={setMinUsageCount}>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="all">Any</SelectItem>
                      <SelectItem value="10">10+</SelectItem>
                      <SelectItem value="20">20+</SelectItem>
                      <SelectItem value="50">50+</SelectItem>
                      <SelectItem value="100">100+</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Tag List */}
        {filteredTags.length > 0 ? (
          <div className="space-y-6">
            {Object.entries(groupedTags).map(([groupName, groupTags]) => (
              <div key={groupName}>
                {/* Group Header */}
                {groupBy !== "none" && (
                  <h3 className="mb-3 text-sm font-semibold text-muted-foreground capitalize">
                    {groupName} ({groupTags.length})
                  </h3>
                )}

                {/* Tag Cards */}
                <div className="space-y-3">
                  {groupTags.map((tag) => (
                    <Link key={tag.id} href={`/tags/${tag.id}`}>
                      <Card className="hover:border-primary/50 cursor-pointer transition-colors">
                        <CardContent className="pt-6">
                          <div className="flex items-start justify-between gap-4">
                            {/* Tag Content */}
                            <div className="flex items-start gap-4 flex-1">
                              {/* Color Indicator */}
                              <div
                                className="h-10 w-10 rounded-lg flex-shrink-0"
                                style={{ backgroundColor: tag.color }}
                              />

                              {/* Tag Info */}
                              <div className="flex-1 space-y-1">
                                <h3 className="font-semibold">{tag.name}</h3>
                                {tag.description && (
                                  <p className="text-sm text-muted-foreground line-clamp-1">
                                    {tag.description}
                                  </p>
                                )}
                                <div className="flex items-center gap-3 text-xs text-muted-foreground">
                                  <span>Total: {tag.usage.total}</span>
                                  {tag.usage.projects > 0 && (
                                    <span>Projects: {tag.usage.projects}</span>
                                  )}
                                  {tag.usage.issues > 0 && (
                                    <span>Issues: {tag.usage.issues}</span>
                                  )}
                                  {tag.usage.milestones > 0 && (
                                    <span>Milestones: {tag.usage.milestones}</span>
                                  )}
                                  {tag.usage.initiatives > 0 && (
                                    <span>Initiatives: {tag.usage.initiatives}</span>
                                  )}
                                  {tag.usage.literature > 0 && (
                                    <span>Literature: {tag.usage.literature}</span>
                                  )}
                                </div>
                              </div>
                            </div>

                            {/* Tag Badge Preview */}
                            <div className="flex-shrink-0">
                              <TagBadge
                                tag={{ id: tag.id, name: tag.name, color: tag.color }}
                                size="md"
                              />
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
              <TagsIcon className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
              <p className="text-sm text-muted-foreground">
                {tags && tags.length > 0
                  ? "No tags match the current filters."
                  : "No tags yet. Create one to start organizing your work!"}
              </p>
              {hasActiveFilters && tags && tags.length > 0 && (
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

      {/* Create Dialog - TODO: Implement */}
      {/* <CreateTagDialog
        open={createDialogOpen}
        onOpenChange={setCreateDialogOpen}
      /> */}
    </PageLayout>
  );
}
