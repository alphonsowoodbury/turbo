"use client";

import { useEffect, useRef, useState } from "react";
import { cn } from "@/lib/utils";

interface ResizableHandleProps {
  onResize: (delta: number) => void;
  minHeight: number;
  maxHeight: number;
  className?: string;
}

export function ResizableHandle({
  onResize,
  minHeight,
  maxHeight,
  className,
}: ResizableHandleProps) {
  const [isDragging, setIsDragging] = useState(false);
  const startYRef = useRef<number>(0);
  const startHeightRef = useRef<number>(0);

  useEffect(() => {
    if (!isDragging) return;

    const handleMouseMove = (e: MouseEvent) => {
      e.preventDefault();
      const delta = startYRef.current - e.clientY; // Inverted because we're resizing upward
      onResize(delta);
    };

    const handleMouseUp = () => {
      setIsDragging(false);
    };

    document.addEventListener("mousemove", handleMouseMove);
    document.addEventListener("mouseup", handleMouseUp);
    document.body.style.cursor = "ns-resize";
    document.body.style.userSelect = "none";

    return () => {
      document.removeEventListener("mousemove", handleMouseMove);
      document.removeEventListener("mouseup", handleMouseUp);
      document.body.style.cursor = "";
      document.body.style.userSelect = "";
    };
  }, [isDragging, onResize]);

  const handleMouseDown = (e: React.MouseEvent) => {
    e.preventDefault();
    startYRef.current = e.clientY;
    setIsDragging(true);
  };

  return (
    <div
      className={cn(
        "group h-1 cursor-ns-resize border-t transition-colors",
        isDragging ? "bg-primary" : "bg-border hover:bg-accent",
        className
      )}
      onMouseDown={handleMouseDown}
      title="Drag to resize"
      role="separator"
      aria-orientation="horizontal"
      aria-label="Resize terminal panel"
    >
      <div
        className={cn(
          "mx-auto h-full w-12 transition-opacity",
          isDragging ? "opacity-100" : "opacity-0 group-hover:opacity-100"
        )}
      />
    </div>
  );
}