"use client";

import { FileText } from "lucide-react";

interface IssueDocumentsTabProps {
  issueId: string;
  projectId: string;
}

export function IssueDocumentsTab({ issueId, projectId }: IssueDocumentsTabProps) {
  return (
    <div className="flex flex-col items-center justify-center py-12 text-center">
      <FileText className="h-12 w-12 text-muted-foreground/30 mb-4" />
      <p className="text-sm text-muted-foreground mb-1">Documents can't be linked to issues yet</p>
      <p className="text-xs text-muted-foreground">
        Documents are currently project-level only
      </p>
    </div>
  );
}
