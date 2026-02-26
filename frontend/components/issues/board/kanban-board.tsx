"use client";

import { useState, useMemo } from "react";
import {
  DndContext,
  DragOverlay,
  DragStartEvent,
  DragEndEvent,
  DragOverEvent,
  PointerSensor,
  TouchSensor,
  KeyboardSensor,
  useSensor,
  useSensors,
  closestCorners,
} from "@dnd-kit/core";
import { sortableKeyboardCoordinates } from "@dnd-kit/sortable";
import { KanbanColumn } from "./kanban-column";
import { KanbanCardOverlay } from "./kanban-card";
import type { Issue, IssueStatus } from "@/lib/types";

const COLUMN_ORDER: IssueStatus[] = [
  "open",
  "ready",
  "in_progress",
  "review",
  "testing",
  "closed",
];

interface KanbanBoardProps {
  issues: Issue[];
  onStatusChange: (issueId: string, newStatus: IssueStatus) => void;
}

export function KanbanBoard({ issues, onStatusChange }: KanbanBoardProps) {
  const [activeId, setActiveId] = useState<string | null>(null);
  const [localIssues, setLocalIssues] = useState<Issue[]>(issues);

  // Sync local state with props when issues change from server
  const issueIds = issues.map((i) => i.id).join(",");
  useMemo(() => {
    setLocalIssues(issues);
  }, [issueIds]); // eslint-disable-line react-hooks/exhaustive-deps

  const sensors = useSensors(
    useSensor(PointerSensor, { activationConstraint: { distance: 5 } }),
    useSensor(TouchSensor, { activationConstraint: { delay: 200, tolerance: 5 } }),
    useSensor(KeyboardSensor, { coordinateGetter: sortableKeyboardCoordinates })
  );

  const columnIssues = useMemo(() => {
    const grouped: Record<string, Issue[]> = {};
    COLUMN_ORDER.forEach((status) => {
      grouped[status] = [];
    });
    localIssues.forEach((issue) => {
      const status = issue.status || "open";
      if (grouped[status]) {
        grouped[status].push(issue);
      } else {
        grouped["open"].push(issue);
      }
    });
    return grouped;
  }, [localIssues]);

  const activeIssue = activeId
    ? localIssues.find((i) => i.id === activeId) || null
    : null;

  function findColumnForIssue(issueId: string): IssueStatus | null {
    for (const status of COLUMN_ORDER) {
      if (columnIssues[status].some((i) => i.id === issueId)) {
        return status;
      }
    }
    return null;
  }

  function handleDragStart(event: DragStartEvent) {
    setActiveId(String(event.active.id));
  }

  function handleDragOver(event: DragOverEvent) {
    const { active, over } = event;
    if (!over) return;

    const activeIssueId = String(active.id);
    const overId = String(over.id);

    // Determine target column - could be dropping on a column or on another card
    let targetStatus: IssueStatus | null = null;
    if (COLUMN_ORDER.includes(overId as IssueStatus)) {
      targetStatus = overId as IssueStatus;
    } else {
      targetStatus = findColumnForIssue(overId);
    }

    if (!targetStatus) return;

    const sourceStatus = findColumnForIssue(activeIssueId);
    if (sourceStatus === targetStatus) return;

    // Optimistically move the issue to the new column
    setLocalIssues((prev) =>
      prev.map((issue) =>
        issue.id === activeIssueId
          ? { ...issue, status: targetStatus as IssueStatus }
          : issue
      )
    );
  }

  function handleDragEnd(event: DragEndEvent) {
    const { active, over } = event;
    setActiveId(null);

    if (!over) return;

    const activeIssueId = String(active.id);
    const overId = String(over.id);

    let targetStatus: IssueStatus | null = null;
    if (COLUMN_ORDER.includes(overId as IssueStatus)) {
      targetStatus = overId as IssueStatus;
    } else {
      targetStatus = findColumnForIssue(overId);
    }

    if (!targetStatus) return;

    // Find the original status from the server issues
    const originalIssue = issues.find((i) => i.id === activeIssueId);
    if (originalIssue && originalIssue.status !== targetStatus) {
      onStatusChange(activeIssueId, targetStatus);
    }
  }

  function handleDragCancel() {
    setActiveId(null);
    setLocalIssues(issues);
  }

  return (
    <DndContext
      sensors={sensors}
      collisionDetection={closestCorners}
      onDragStart={handleDragStart}
      onDragOver={handleDragOver}
      onDragEnd={handleDragEnd}
      onDragCancel={handleDragCancel}
    >
      <div className="flex gap-3 overflow-x-auto snap-x snap-mandatory pb-4 md:snap-none">
        {COLUMN_ORDER.map((status) => (
          <KanbanColumn
            key={status}
            status={status}
            issues={columnIssues[status]}
          />
        ))}
      </div>

      <DragOverlay>
        {activeIssue ? <KanbanCardOverlay issue={activeIssue} /> : null}
      </DragOverlay>
    </DndContext>
  );
}
