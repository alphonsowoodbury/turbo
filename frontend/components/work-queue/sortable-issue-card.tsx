"use client";

import { useSortable } from "@dnd-kit/sortable";
import { CSS } from "@dnd-kit/utilities";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { GripVertical, Eye, X } from "lucide-react";

interface Issue {
  id: string;
  issue_key?: string | null;
  title: string;
  description: string;
  type: string;
  status: string;
  priority: string;
  work_rank: number | null;
}

interface SortableIssueCardProps {
  issue: Issue;
  onRemove: () => void;
  onView: () => void;
}

export function SortableIssueCard({ issue, onRemove, onView }: SortableIssueCardProps) {
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
    <div ref={setNodeRef} style={style}>
      <Card className={`${isDragging ? "shadow-lg" : ""}`}>
        <CardContent className="p-4">
          <div className="flex items-start gap-3">
            {/* Drag Handle */}
            <button
              className="mt-1 cursor-grab active:cursor-grabbing touch-none"
              {...attributes}
              {...listeners}
            >
              <GripVertical className="h-5 w-5 text-muted-foreground" />
            </button>

            {/* Rank Badge */}
            <div className="flex-shrink-0 mt-1">
              <Badge variant="outline" className="font-mono">
                #{issue.work_rank}
              </Badge>
            </div>

            {/* Issue Content */}
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2 mb-1">
                {issue.issue_key && (
                  <Badge variant="outline" className="font-mono text-xs">
                    {issue.issue_key}
                  </Badge>
                )}
                <h3 className="font-semibold text-base line-clamp-1">
                  {issue.title}
                </h3>
              </div>
              <p className="text-sm text-muted-foreground line-clamp-2 mb-3">
                {issue.description}
              </p>
              <div className="flex flex-wrap items-center gap-2">
                <Badge
                  variant={
                    issue.priority === "critical" || issue.priority === "high"
                      ? "destructive"
                      : "secondary"
                  }
                >
                  {issue.priority}
                </Badge>
                <Badge variant="outline">{issue.status}</Badge>
                <Badge variant="secondary">{issue.type}</Badge>
              </div>
            </div>

            {/* Action Buttons */}
            <div className="flex flex-col gap-2">
              <Button
                variant="ghost"
                size="icon"
                onClick={onView}
                title="View Issue"
              >
                <Eye className="h-4 w-4" />
              </Button>
              <Button
                variant="ghost"
                size="icon"
                onClick={onRemove}
                title="Remove from Queue"
              >
                <X className="h-4 w-4" />
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
