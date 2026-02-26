"use client";

import { useDroppable } from "@dnd-kit/core";
import { SortableContext, verticalListSortingStrategy } from "@dnd-kit/sortable";
import { cn } from "@/lib/utils";
import { KanbanCard } from "./kanban-card";
import type { Issue, IssueStatus } from "@/lib/types";

const statusConfig: Record<string, { label: string; dotColor: string }> = {
  open: { label: "Open", dotColor: "bg-green-500" },
  ready: { label: "Ready", dotColor: "bg-cyan-500" },
  in_progress: { label: "In Progress", dotColor: "bg-blue-500" },
  review: { label: "Review", dotColor: "bg-purple-500" },
  testing: { label: "Testing", dotColor: "bg-orange-500" },
  closed: { label: "Closed", dotColor: "bg-gray-500" },
};

interface KanbanColumnProps {
  status: IssueStatus;
  issues: Issue[];
}

export function KanbanColumn({ status, issues }: KanbanColumnProps) {
  const { setNodeRef, isOver } = useDroppable({ id: status });
  const config = statusConfig[status] || { label: status, dotColor: "bg-gray-500" };

  return (
    <div
      className={cn(
        "flex min-h-[200px] w-[280px] flex-shrink-0 snap-center flex-col rounded-lg bg-muted/30 md:flex-1 md:w-auto md:min-w-[200px]",
        isOver && "ring-2 ring-primary/50"
      )}
    >
      <div className="flex items-center gap-2 px-3 py-2.5 border-b">
        <span className={cn("h-2 w-2 rounded-full", config.dotColor)} />
        <span className="text-sm font-medium">{config.label}</span>
        <span className="ml-auto rounded-full bg-muted px-2 py-0.5 text-xs font-medium text-muted-foreground">
          {issues.length}
        </span>
      </div>

      <div
        ref={setNodeRef}
        className="flex-1 space-y-2 overflow-y-auto p-2"
      >
        <SortableContext
          items={issues.map((i) => i.id)}
          strategy={verticalListSortingStrategy}
        >
          {issues.map((issue) => (
            <KanbanCard key={issue.id} issue={issue} />
          ))}
        </SortableContext>
      </div>
    </div>
  );
}
