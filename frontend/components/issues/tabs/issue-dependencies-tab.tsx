"use client";

import { useState } from "react";
import Link from "next/link";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Loader2, Plus, X } from "lucide-react";
import { useIssue, useIssues } from "@/hooks/use-issues";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import {
  Command,
  CommandEmpty,
  CommandGroup,
  CommandInput,
  CommandItem,
} from "@/components/ui/command";
import { toast } from "sonner";

interface IssueDependenciesTabProps {
  issueId: string;
  blocking: string[];
  blockedBy: string[];
}

export function IssueDependenciesTab({ issueId, blocking, blockedBy }: IssueDependenciesTabProps) {
  const [addBlockingOpen, setAddBlockingOpen] = useState(false);
  const [addBlockedOpen, setAddBlockedOpen] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");
  const { data: allIssues } = useIssues();

  const handleAddDependency = async (blockingIssueId: string, blockedIssueId: string) => {
    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/dependencies/`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          blocking_issue_id: blockingIssueId,
          blocked_issue_id: blockedIssueId,
          dependency_type: "blocks",
        }),
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || "Failed to add dependency");
      }

      toast.success("Dependency added successfully");
      setAddBlockingOpen(false);
      setAddBlockedOpen(false);
      setSearchQuery("");

      // Refresh the page to show updated dependencies
      window.location.reload();
    } catch (error) {
      toast.error(error instanceof Error ? error.message : "Failed to add dependency");
    }
  };

  const handleRemoveDependency = async (blockingIssueId: string, blockedIssueId: string) => {
    try {
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/dependencies/${blockingIssueId}/${blockedIssueId}`,
        { method: "DELETE" }
      );

      if (!response.ok) {
        throw new Error("Failed to remove dependency");
      }

      toast.success("Dependency removed successfully");

      // Refresh the page to show updated dependencies
      window.location.reload();
    } catch (error) {
      toast.error(error instanceof Error ? error.message : "Failed to remove dependency");
    }
  };

  // Filter out current issue and already linked issues
  const availableBlockingIssues = allIssues?.filter(
    (issue) => issue.id !== issueId && !blocking.includes(issue.id)
  ) || [];

  const availableBlockedIssues = allIssues?.filter(
    (issue) => issue.id !== issueId && !blockedBy.includes(issue.id)
  ) || [];

  if (blocking.length === 0 && blockedBy.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-12 text-center">
        <X className="h-12 w-12 text-muted-foreground/30 mb-4" />
        <p className="text-sm text-muted-foreground mb-1">No dependencies</p>
        <p className="text-xs text-muted-foreground">
          Add blocking or blocked issues to track dependencies
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-6 py-4">
      {/* Blocked By */}
      <div>
        <div className="flex items-center justify-between mb-3">
          <h3 className="text-sm font-medium">Blocked By</h3>
          <Dialog open={addBlockingOpen} onOpenChange={setAddBlockingOpen}>
            <DialogTrigger asChild>
              <Button variant="outline" size="sm">
                <Plus className="h-3 w-3 mr-1" />
                Add
              </Button>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>Add Blocking Issue</DialogTitle>
                <DialogDescription>
                  Select an issue that blocks this one from being worked on.
                </DialogDescription>
              </DialogHeader>
              <Command>
                <CommandInput
                  placeholder="Search issues..."
                  value={searchQuery}
                  onValueChange={setSearchQuery}
                />
                <CommandEmpty>No issues found.</CommandEmpty>
                <CommandGroup className="max-h-64 overflow-y-auto">
                  {availableBlockingIssues.map((issue) => (
                    <CommandItem
                      key={issue.id}
                      value={issue.title}
                      onSelect={() => handleAddDependency(issue.id, issueId)}
                      className="cursor-pointer"
                    >
                      <div className="flex flex-col">
                        <span className="font-medium">{issue.title}</span>
                        <div className="flex gap-1 mt-1">
                          <Badge variant="secondary" className="text-[10px] h-4 px-1">
                            {issue.type}
                          </Badge>
                          <Badge variant="secondary" className="text-[10px] h-4 px-1">
                            {issue.priority}
                          </Badge>
                        </div>
                      </div>
                    </CommandItem>
                  ))}
                </CommandGroup>
              </Command>
            </DialogContent>
          </Dialog>
        </div>
        {blocking.length === 0 ? (
          <p className="text-sm text-muted-foreground">No blocking dependencies</p>
        ) : (
          <div className="space-y-2">
            {blocking.map((blockingId) => (
              <DependencyItem
                key={blockingId}
                issueId={blockingId}
                onRemove={() => handleRemoveDependency(blockingId, issueId)}
              />
            ))}
          </div>
        )}
      </div>

      {/* Blocks */}
      <div>
        <div className="flex items-center justify-between mb-3">
          <h3 className="text-sm font-medium">Blocks</h3>
          <Dialog open={addBlockedOpen} onOpenChange={setAddBlockedOpen}>
            <DialogTrigger asChild>
              <Button variant="outline" size="sm">
                <Plus className="h-3 w-3 mr-1" />
                Add
              </Button>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>Add Blocked Issue</DialogTitle>
                <DialogDescription>
                  Select an issue that this one blocks from being worked on.
                </DialogDescription>
              </DialogHeader>
              <Command>
                <CommandInput
                  placeholder="Search issues..."
                  value={searchQuery}
                  onValueChange={setSearchQuery}
                />
                <CommandEmpty>No issues found.</CommandEmpty>
                <CommandGroup className="max-h-64 overflow-y-auto">
                  {availableBlockedIssues.map((issue) => (
                    <CommandItem
                      key={issue.id}
                      value={issue.title}
                      onSelect={() => handleAddDependency(issueId, issue.id)}
                      className="cursor-pointer"
                    >
                      <div className="flex flex-col">
                        <span className="font-medium">{issue.title}</span>
                        <div className="flex gap-1 mt-1">
                          <Badge variant="secondary" className="text-[10px] h-4 px-1">
                            {issue.type}
                          </Badge>
                          <Badge variant="secondary" className="text-[10px] h-4 px-1">
                            {issue.priority}
                          </Badge>
                        </div>
                      </div>
                    </CommandItem>
                  ))}
                </CommandGroup>
              </Command>
            </DialogContent>
          </Dialog>
        </div>
        {blockedBy.length === 0 ? (
          <p className="text-sm text-muted-foreground">No blocked dependencies</p>
        ) : (
          <div className="space-y-2">
            {blockedBy.map((blockedId) => (
              <DependencyItem
                key={blockedId}
                issueId={blockedId}
                onRemove={() => handleRemoveDependency(issueId, blockedId)}
              />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

interface DependencyItemProps {
  issueId: string;
  onRemove: () => void;
}

function DependencyItem({ issueId, onRemove }: DependencyItemProps) {
  const { data: issue, isLoading } = useIssue(issueId);

  if (isLoading) {
    return (
      <div className="flex items-center justify-between p-2 rounded-md border bg-muted/50">
        <Loader2 className="h-4 w-4 animate-spin" />
      </div>
    );
  }

  if (!issue) {
    return null;
  }

  return (
    <div className="flex items-center justify-between p-2 rounded-md border hover:bg-muted/50 transition-colors group">
      <Link href={`/issues/${issue.id}`} className="flex-1 min-w-0">
        <div className="flex items-center gap-2">
          <span className="text-sm font-medium truncate">{issue.title}</span>
          <Badge variant="secondary" className="text-[10px] h-4 px-1 shrink-0">
            {issue.status}
          </Badge>
        </div>
      </Link>
      <Button
        variant="ghost"
        size="sm"
        onClick={onRemove}
        className="h-6 w-6 p-0 opacity-0 group-hover:opacity-100 transition-opacity"
      >
        <X className="h-3 w-3" />
      </Button>
    </div>
  );
}
