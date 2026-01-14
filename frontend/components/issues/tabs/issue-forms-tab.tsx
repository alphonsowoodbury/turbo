"use client";

import { IssueFormsSection } from "@/components/forms/issue-forms-section";

interface IssueFormsTabProps {
  issueId: string;
}

export function IssueFormsTab({ issueId }: IssueFormsTabProps) {
  return (
    <div className="py-4">
      <IssueFormsSection issueId={issueId} />
    </div>
  );
}
