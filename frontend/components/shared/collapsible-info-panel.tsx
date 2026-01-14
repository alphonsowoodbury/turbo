"use client";

import { useEffect } from "react";
import { Collapsible, CollapsibleContent } from "@/components/ui/collapsible";
import { cn } from "@/lib/utils";

interface CollapsibleInfoPanelProps {
  isOpen: boolean;
  onToggle: (open: boolean) => void;
  children: React.ReactNode;
  className?: string;
  storageKey?: string; // Key for localStorage persistence
}

/**
 * CollapsibleInfoPanel Component
 *
 * A reusable collapsible panel that slides down from under the header.
 * Useful for showing entity metadata and details without cluttering the main content.
 *
 * Features:
 * - Smooth slide-down animation (~250ms)
 * - Optional localStorage persistence
 * - Accessible via Radix UI Collapsible
 * - Customizable styling via className
 *
 * Usage:
 * ```tsx
 * <CollapsibleInfoPanel
 *   isOpen={isOpen}
 *   onToggle={setIsOpen}
 *   storageKey="mentor-info-panel"
 * >
 *   <div>Your content here</div>
 * </CollapsibleInfoPanel>
 * ```
 */
export function CollapsibleInfoPanel({
  isOpen,
  onToggle,
  children,
  className,
  storageKey,
}: CollapsibleInfoPanelProps) {
  // Load persisted state from localStorage on mount
  useEffect(() => {
    if (storageKey && typeof window !== "undefined") {
      const stored = localStorage.getItem(storageKey);
      if (stored !== null) {
        const isStoredOpen = stored === "true";
        if (isStoredOpen !== isOpen) {
          onToggle(isStoredOpen);
        }
      }
    }
  }, [storageKey]); // Only run on mount

  // Persist state to localStorage when it changes
  useEffect(() => {
    if (storageKey && typeof window !== "undefined") {
      localStorage.setItem(storageKey, String(isOpen));
    }
  }, [isOpen, storageKey]);

  return (
    <Collapsible open={isOpen} onOpenChange={onToggle}>
      <CollapsibleContent
        className={cn(
          "overflow-hidden border-b bg-background",
          "data-[state=closed]:animate-collapsible-up",
          "data-[state=open]:animate-collapsible-down",
          className
        )}
      >
        {children}
      </CollapsibleContent>
    </Collapsible>
  );
}
