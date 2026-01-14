"use client";

import { useState, useRef, useEffect } from "react";
import { CommentList } from "@/components/issues/comment-list";
import { Button } from "@/components/ui/button";
import { ChevronDown, ChevronUp, GripHorizontal } from "lucide-react";
import { cn } from "@/lib/utils";
import type { EntityType } from "@/lib/types";

interface EntityCommentsSectionProps {
  entityType: EntityType;
  entityId: string;
  defaultHeight?: number; // Default height in pixels, defaults to 500
  minHeight?: number; // Minimum height in pixels, defaults to 200
  maxHeight?: number; // Maximum height in pixels, defaults to 800
  title?: string; // Custom title, defaults to "Comments"
}

/**
 * Reusable comments section for any entity.
 *
 * Features:
 * - Collapsible (expand/collapse)
 * - User-adjustable height (drag to resize)
 * - Fixed height container with independent scroll
 * - Compact scrollable comments list
 * - Fixed input at bottom that auto-expands
 * - Consistent UX across all entity types
 *
 * Usage:
 * ```tsx
 * <EntityCommentsSection
 *   entityType="issue"
 *   entityId={issueId}
 *   defaultHeight={500}
 *   minHeight={200}
 *   maxHeight={800}
 * />
 * ```
 */
export function EntityCommentsSection({
  entityType,
  entityId,
  defaultHeight = 500,
  minHeight = 200,
  maxHeight = 800,
  title = "Comments",
}: EntityCommentsSectionProps) {
  // Load persisted state from localStorage on mount
  const [isCollapsed, setIsCollapsed] = useState(() => {
    if (typeof window !== "undefined") {
      const saved = localStorage.getItem("commentsPane:isCollapsed");
      return saved !== null ? saved === "true" : false; // Default to open (false)
    }
    return false; // Default to open
  });

  const [height, setHeight] = useState(() => {
    if (typeof window !== "undefined") {
      const saved = localStorage.getItem("commentsPane:height");
      return saved ? parseInt(saved, 10) : defaultHeight;
    }
    return defaultHeight;
  });

  const [isResizing, setIsResizing] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);
  const startYRef = useRef(0);
  const startHeightRef = useRef(0);

  // Persist collapsed state to localStorage
  useEffect(() => {
    localStorage.setItem("commentsPane:isCollapsed", String(isCollapsed));
  }, [isCollapsed]);

  // Persist height to localStorage
  useEffect(() => {
    localStorage.setItem("commentsPane:height", String(height));
  }, [height]);

  // Handle resize start
  const handleResizeStart = (e: React.MouseEvent) => {
    e.preventDefault();
    setIsResizing(true);
    startYRef.current = e.clientY;
    startHeightRef.current = height;
  };

  // Handle resize during drag
  useEffect(() => {
    if (!isResizing) return;

    const handleMouseMove = (e: MouseEvent) => {
      const deltaY = startYRef.current - e.clientY; // Inverted because top drag
      const newHeight = Math.min(
        Math.max(startHeightRef.current + deltaY, minHeight),
        maxHeight
      );
      setHeight(newHeight);
    };

    const handleMouseUp = () => {
      setIsResizing(false);
    };

    document.addEventListener("mousemove", handleMouseMove);
    document.addEventListener("mouseup", handleMouseUp);

    return () => {
      document.removeEventListener("mousemove", handleMouseMove);
      document.removeEventListener("mouseup", handleMouseUp);
    };
  }, [isResizing, minHeight, maxHeight]);

  // Add cursor style when resizing
  useEffect(() => {
    if (isResizing) {
      document.body.style.cursor = "ns-resize";
      document.body.style.userSelect = "none";
    } else {
      document.body.style.cursor = "";
      document.body.style.userSelect = "";
    }
  }, [isResizing]);

  return (
    <div
      ref={containerRef}
      className="flex-shrink-0 border-t bg-background flex flex-col transition-all duration-200"
      style={{ height: isCollapsed ? "auto" : `${height}px` }}
    >
      {/* Resize Handle */}
      {!isCollapsed && (
        <div
          className={cn(
            "h-1.5 cursor-ns-resize hover:bg-primary/20 active:bg-primary/30 transition-colors flex items-center justify-center group",
            isResizing && "bg-primary/30"
          )}
          onMouseDown={handleResizeStart}
        >
          <GripHorizontal className="h-3 w-3 text-muted-foreground opacity-0 group-hover:opacity-100 transition-opacity" />
        </div>
      )}

      {/* Header */}
      <div className="px-4 py-3 border-b flex-shrink-0 flex items-center justify-between">
        <h2 className="text-sm font-semibold">{title}</h2>
        <Button
          variant="ghost"
          size="sm"
          onClick={() => setIsCollapsed(!isCollapsed)}
          className="h-6 w-6 p-0"
        >
          {isCollapsed ? (
            <ChevronUp className="h-4 w-4" />
          ) : (
            <ChevronDown className="h-4 w-4" />
          )}
        </Button>
      </div>

      {/* Comments List with fixed input */}
      {!isCollapsed && (
        <div className="flex-1 overflow-hidden">
          <CommentList entityType={entityType} entityId={entityId} />
        </div>
      )}
    </div>
  );
}
