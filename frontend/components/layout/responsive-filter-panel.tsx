"use client";

import { ReactNode } from "react";
import { Card, CardContent } from "@/components/ui/card";
import { useIsMobile } from "@/hooks/use-mobile";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";

interface ResponsiveFilterPanelProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  children: ReactNode;
  title?: string;
}

export function ResponsiveFilterPanel({
  open,
  onOpenChange,
  children,
  title = "Filters",
}: ResponsiveFilterPanelProps) {
  const isMobile = useIsMobile();

  if (!open) return null;

  if (isMobile) {
    return (
      <Dialog open={open} onOpenChange={onOpenChange}>
        <DialogContent className="bottom-0 top-auto translate-y-0 rounded-b-none rounded-t-xl data-[state=closed]:slide-out-to-bottom data-[state=open]:slide-in-from-bottom sm:bottom-auto sm:top-1/2 sm:-translate-y-1/2 sm:rounded-lg">
          <DialogHeader>
            <DialogTitle>{title}</DialogTitle>
          </DialogHeader>
          <div className="grid grid-cols-1 gap-4">{children}</div>
        </DialogContent>
      </Dialog>
    );
  }

  return (
    <Card className="mb-4">
      <CardContent className="pt-6">
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 md:grid-cols-4">
          {children}
        </div>
      </CardContent>
    </Card>
  );
}
