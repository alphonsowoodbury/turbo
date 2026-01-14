"use client";

import { Paperclip } from "lucide-react";
import { Button } from "@/components/ui/button";

interface IssueAttachmentsTabProps {
  issueId: string;
}

export function IssueAttachmentsTab({ issueId }: IssueAttachmentsTabProps) {
  return (
    <div className="flex flex-col items-center justify-center py-12 text-center">
      <Paperclip className="h-12 w-12 text-muted-foreground/30 mb-4" />
      <p className="text-sm text-muted-foreground mb-1">Attachments Coming Soon</p>
      <p className="text-xs text-muted-foreground">
        File attachment support will be added in a future update
      </p>
    </div>
  );
}
