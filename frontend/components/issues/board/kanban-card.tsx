"use client";

import { useSortable } from "@dnd-kit/sortable";
import { CSS } from "@dnd-kit/utilities";
import Link from "next/link";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import type { Issue } from "@/lib/types";

const priorityColors: Record<string, string> = {
  low: "bg-blue-500/10 text-blue-500",
  medium: "bg-yellow-500/10 text-yellow-500",
  high: "bg-orange-500/10 text-orange-500",
  critical: "bg-red-500/10 text-red-500",
};

interface KanbanCardProps {
  issue: Issue;
}

export function KanbanCard({ issue }: KanbanCardProps) {
  const {
    attributes,
    listeners,
    setNodeRef,
    transform,
    transition,
    isDragging,
  } = useSortable({ id: issue.id });

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
    opacity: isDragging ? 0.5 : 1,
  };

  return (
    <div
      ref={setNodeRef}
      style={style}
      {...attributes}
      {...listeners}
      className={cn(
        "touch-manipulation rounded-lg border bg-card p-3 shadow-sm cursor-grab active:cursor-grabbing active:shadow-lg",
        isDragging && "shadow-lg ring-2 ring-primary/30"
      )}
    >
      <Link
        href={`/issues/${issue.id}`}
        onClick={(e) => {
          // Don't navigate if we're dragging
          if (isDragging) e.preventDefault();
        }}
        className="block"
      >
        <div className="space-y-2">
          {issue.issue_key && (
            <span className="font-mono text-[10px] text-muted-foreground">
              {issue.issue_key}
            </span>
          )}
          <p className="text-sm font-medium leading-tight line-clamp-2">
            {issue.title}
          </p>
          <div className="flex items-center gap-1.5 flex-wrap">
            <Badge
              variant="secondary"
              className={cn("text-[10px] px-1.5 py-0", priorityColors[issue.priority || "medium"])}
            >
              {issue.priority}
            </Badge>
            {issue.assignee && (
              <span
                className="flex h-5 w-5 items-center justify-center rounded-full bg-muted text-[10px] font-medium"
                title={issue.assignee}
              >
                {issue.assignee.charAt(0).toUpperCase()}
              </span>
            )}
          </div>
        </div>
      </Link>
    </div>
  );
}

export function KanbanCardOverlay({ issue }: { issue: Issue }) {
  return (
    <div className="rounded-lg border bg-card p-3 shadow-xl ring-2 ring-primary/30">
      <div className="space-y-2">
        {issue.issue_key && (
          <span className="font-mono text-[10px] text-muted-foreground">
            {issue.issue_key}
          </span>
        )}
        <p className="text-sm font-medium leading-tight line-clamp-2">
          {issue.title}
        </p>
        <div className="flex items-center gap-1.5">
          <Badge
            variant="secondary"
            className={cn("text-[10px] px-1.5 py-0", priorityColors[issue.priority || "medium"])}
          >
            {issue.priority}
          </Badge>
        </div>
      </div>
    </div>
  );
}
