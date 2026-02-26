"use client";

import { Suspense, useState, useMemo } from "react";
import { PageLayout } from "@/components/layout/page-layout";
import { Card, CardContent } from "@/components/ui/card";
import { useWorktrees, useDeleteWorktree } from "@/hooks/use-worktrees";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Filter,
  X,
  GitBranch,
  Lock,
  Unlock,
  Folder,
  AlertCircle,
  Trash2,
  ExternalLink
} from "lucide-react";
import { cn } from "@/lib/utils";
import { toast } from "sonner";

const getStatusIcon = (isLocked: boolean) => {
  return isLocked ? <Lock className="h-4 w-4" /> : <Unlock className="h-4 w-4" />;
};

const getStatusColor = (isLocked: boolean) => {
  return isLocked ? "destructive" : "default";
};

function WorktreesContent() {
  const [showFilters, setShowFilters] = useState(false);
  const [selectedStatus, setSelectedStatus] = useState<string>("all");
  const [sortBy, setSortBy] = useState<string>("issue_key");

  const { data, isLoading } = useWorktrees();
  const deleteWorktree = useDeleteWorktree();

  const worktrees = data?.worktrees || [];
  const basePath = data?.worktree_base_path || "";

  // Apply filters
  const filteredWorktrees = useMemo(() => {
    let filtered = [...worktrees];

    if (selectedStatus === "locked") {
      filtered = filtered.filter((w) => w.is_locked);
    } else if (selectedStatus === "unlocked") {
      filtered = filtered.filter((w) => !w.is_locked);
    }

    return filtered;
  }, [worktrees, selectedStatus]);

  // Sort worktrees
  const sortedWorktrees = useMemo(() => {
    const sorted = [...filteredWorktrees];

    switch (sortBy) {
      case "issue_key":
        return sorted.sort((a, b) => {
          const keyA = a.issue_key || "";
          const keyB = b.issue_key || "";
          return keyA.localeCompare(keyB);
        });
      case "branch":
        return sorted.sort((a, b) => a.branch.localeCompare(b.branch));
      case "path":
        return sorted.sort((a, b) => a.path.localeCompare(b.path));
      default:
        return sorted;
    }
  }, [filteredWorktrees, sortBy]);

  const hasActiveFilters = selectedStatus !== "all";

  const clearFilters = () => {
    setSelectedStatus("all");
  };

  const handleDelete = async (issueKey: string | null) => {
    if (!issueKey) {
      toast.error("Cannot delete worktree without issue key");
      return;
    }

    if (!confirm(`Delete worktree for ${issueKey}? This will remove the directory and git references.`)) {
      return;
    }

    try {
      await deleteWorktree.mutateAsync(issueKey);
      toast.success(`Worktree for ${issueKey} deleted`);
    } catch (error) {
      toast.error(error instanceof Error ? error.message : "Failed to delete worktree");
    }
  };

  const openInFinder = (path: string) => {
    // This would need to be implemented with a native bridge or file:// protocol
    window.open(`file://${path}`, "_blank");
  };

  return (
    <PageLayout
      title="Git Worktrees"
      isLoading={isLoading}
    >
      <div className="page-padding">
        {/* Controls Bar */}
        <div className="mb-4 flex items-center justify-between">
          <div className="text-sm text-muted-foreground">
            {worktrees.length} total worktrees
            {basePath && (
              <span className="ml-2 text-xs opacity-70">
                @ {basePath}
              </span>
            )}
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
                  1
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
                <SelectItem value="issue_key">Issue Key</SelectItem>
                <SelectItem value="branch">Branch</SelectItem>
                <SelectItem value="path">Path</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </div>

        {/* Filter Controls */}
        {showFilters && (
          <Card className="mb-4">
            <CardContent className="pt-6">
              <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 md:grid-cols-3">
                <div className="space-y-2">
                  <label className="text-sm font-medium">Status</label>
                  <Select value={selectedStatus} onValueChange={setSelectedStatus}>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="all">All Statuses</SelectItem>
                      <SelectItem value="locked">Locked</SelectItem>
                      <SelectItem value="unlocked">Unlocked</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Worktrees List */}
        {sortedWorktrees.length > 0 ? (
          <div className="space-y-3">
            {sortedWorktrees.map((worktree) => (
              <Card
                key={worktree.path}
                className="hover:border-primary/50 transition-colors"
              >
                <CardContent className="pt-6">
                  <div className="flex items-start justify-between gap-4">
                    <div className="flex-1 space-y-2">
                      <div className="flex items-center gap-2">
                        {worktree.issue_key && (
                          <Badge variant="outline" className="font-mono text-xs">
                            {worktree.issue_key}
                          </Badge>
                        )}
                        <h3 className="font-semibold text-sm">
                          {worktree.branch}
                        </h3>
                      </div>

                      <div className="flex items-center gap-4 text-xs text-muted-foreground">
                        <span className="flex items-center gap-1">
                          <Folder className="h-3 w-3" />
                          {worktree.path.split('/').pop()}
                        </span>
                        <span className="flex items-center gap-1">
                          <GitBranch className="h-3 w-3" />
                          {worktree.commit_hash}
                        </span>
                      </div>

                      <div className="text-xs text-muted-foreground font-mono opacity-70">
                        {worktree.path}
                      </div>
                    </div>

                    <div className="flex gap-2 items-start">
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => openInFinder(worktree.path)}
                        title="Open in Finder"
                      >
                        <ExternalLink className="h-4 w-4" />
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => handleDelete(worktree.issue_key)}
                        disabled={deleteWorktree.isPending}
                        title="Delete worktree"
                      >
                        <Trash2 className="h-4 w-4 text-destructive" />
                      </Button>
                      <Badge
                        variant={getStatusColor(worktree.is_locked)}
                        className="text-xs capitalize gap-1"
                      >
                        {getStatusIcon(worktree.is_locked)}
                        {worktree.is_locked ? "Locked" : "Active"}
                      </Badge>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}

            {/* Summary */}
            <div className="pt-6 border-t">
              <div className="flex items-center justify-between text-sm text-muted-foreground">
                <span>
                  Showing {sortedWorktrees.length} of {worktrees.length} worktrees
                </span>
                <span>
                  {worktrees.filter(w => w.is_locked).length} locked
                </span>
              </div>
            </div>
          </div>
        ) : (
          <div className="flex h-64 items-center justify-center">
            <div className="text-center">
              <AlertCircle className="h-16 w-16 mx-auto mb-4 opacity-20" />
              <p className="text-sm text-muted-foreground">
                {worktrees && worktrees.length > 0
                  ? "No worktrees match the current filters."
                  : "No git worktrees found."}
              </p>
              {hasActiveFilters && worktrees && worktrees.length > 0 && (
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
    </PageLayout>
  );
}

export default function WorktreesPage() {
  return (
    <Suspense fallback={
      <PageLayout title="Git Worktrees" isLoading={true}>
        <div className="page-padding">
          <div className="flex h-64 items-center justify-center">
            <div className="text-sm text-muted-foreground">Loading worktrees...</div>
          </div>
        </div>
      </PageLayout>
    }>
      <WorktreesContent />
    </Suspense>
  );
}
