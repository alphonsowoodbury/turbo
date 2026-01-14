/**
 * Subagent Button Component
 *
 * Trigger button for opening the subagent dialog
 */

"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Sparkles } from "lucide-react";
import { SubagentDialog } from "./subagent-dialog";
import { cn } from "@/lib/utils";

interface SubagentButtonProps {
  context?: Record<string, any>;
  suggestedAgent?: string;
  suggestedPrompt?: string;
  variant?: "default" | "ghost" | "outline" | "secondary";
  size?: "default" | "sm" | "lg" | "icon";
  className?: string;
  children?: React.ReactNode;
}

export function SubagentButton({
  context,
  suggestedAgent,
  suggestedPrompt,
  variant = "outline",
  size = "sm",
  className,
  children,
}: SubagentButtonProps) {
  const [dialogOpen, setDialogOpen] = useState(false);

  return (
    <>
      <Button
        variant={variant}
        size={size}
        onClick={() => setDialogOpen(true)}
        className={cn("gap-2", className)}
      >
        <Sparkles className="h-4 w-4" />
        {children || "AI Assist"}
      </Button>

      <SubagentDialog
        open={dialogOpen}
        onOpenChange={setDialogOpen}
        context={context}
        suggestedAgent={suggestedAgent}
        suggestedPrompt={suggestedPrompt}
      />
    </>
  );
}
