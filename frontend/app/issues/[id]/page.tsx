"use client";

import { useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { PageLayout } from "@/components/layout/page-layout";
import { useIssue, useDeleteIssue, useCloseIssue, useUpdateIssue } from "@/hooks/use-issues";
import { useProject } from "@/hooks/use-projects";
import { EntityCommentsSection } from "@/components/shared/entity-comments-section";
import { EditIssueDialog } from "@/components/issues/edit-issue-dialog";
import { IssueDependenciesTab } from "@/components/issues/tabs/issue-dependencies-tab";
import { IssueFormsTab } from "@/components/issues/tabs/issue-forms-tab";
import { IssueDocumentsTab } from "@/components/issues/tabs/issue-documents-tab";
import { IssueAttachmentsTab } from "@/components/issues/tabs/issue-attachments-tab";
import { MarkdownRenderer } from "@/components/ui/markdown-renderer";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuRadioGroup,
  DropdownMenuRadioItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Pencil, Star } from "lucide-react";
import { cn } from "@/lib/utils";
import { formatDistanceToNow } from "date-fns";
import { toast } from "sonner";
import { useIsFavorite, useToggleFavorite } from "@/hooks/use-favorites";
import { SubagentButton } from "@/components/subagent/subagent-button";

const priorityColors: Record<string, string> = {
  low: "bg-blue-500/10 text-blue-500 hover:bg-blue-500/20",
  medium: "bg-yellow-500/10 text-yellow-500 hover:bg-yellow-500/20",
  high: "bg-orange-500/10 text-orange-500 hover:bg-orange-500/20",
  critical: "bg-red-500/10 text-red-500 hover:bg-red-500/20",
};

const statusColors: Record<string, string> = {
  open: "bg-green-500/10 text-green-500 hover:bg-green-500/20",
  ready: "bg-cyan-500/10 text-cyan-500 hover:bg-cyan-500/20",
  in_progress: "bg-blue-500/10 text-blue-500 hover:bg-blue-500/20",
  review: "bg-purple-500/10 text-purple-500 hover:bg-purple-500/20",
  testing: "bg-orange-500/10 text-orange-500 hover:bg-orange-500/20",
  closed: "bg-gray-500/10 text-gray-500 hover:bg-gray-500/20",
};

const typeColors: Record<string, string> = {
  feature: "bg-purple-500/10 text-purple-500",
  bug: "bg-red-500/10 text-red-500",
  task: "bg-blue-500/10 text-blue-500",
  enhancement: "bg-green-500/10 text-green-500",
  documentation: "bg-gray-500/10 text-gray-500",
  discovery: "bg-indigo-500/10 text-indigo-500",
};

const discoveryStatusColors: Record<string, string> = {
  proposed: "bg-purple-500/10 text-purple-500 hover:bg-purple-500/20",
  researching: "bg-indigo-500/10 text-indigo-500 hover:bg-indigo-500/20",
  findings_ready: "bg-violet-500/10 text-violet-500 hover:bg-violet-500/20",
  approved: "bg-green-500/10 text-green-500 hover:bg-green-500/20",
  parked: "bg-yellow-500/10 text-yellow-500 hover:bg-yellow-500/20",
  declined: "bg-gray-500/10 text-gray-500 hover:bg-gray-500/20",
};

export default function IssueDetailPage() {
  const params = useParams();
  const router = useRouter();
  const issueId = params.id as string;
  const [editDialogOpen, setEditDialogOpen] = useState(false);

  const { data: issue, isLoading, error } = useIssue(issueId);
  const { data: project } = useProject(issue?.project_id || null);
  const updateIssue = useUpdateIssue();
  const isFavorite = useIsFavorite("issue", issueId);
  const { toggle: toggleFavorite } = useToggleFavorite();

  // Early return if no issue data
  if (!issue) {
    return (
      <PageLayout
        title="Issue Not Found"
        isLoading={isLoading}
        error={error || new Error("Issue not found or failed to load")}
      >
        <div />
      </PageLayout>
    );
  }

  return (
    <PageLayout
      title={issue.title}
      isLoading={isLoading}
      error={error}
      breadcrumbs={project ? [{ label: project.name, href: `/projects/${project.id}` }] : undefined}
    >
      <div className="flex flex-col h-full overflow-hidden">
        {/* Scrollable Content Area */}
        <div className="flex-1 overflow-y-auto space-y-4 p-6 pb-0">
          {/* Issue Metadata */}
          <div className="flex flex-wrap items-center gap-2">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => toggleFavorite("issue", issueId, isFavorite)}
            className="h-4 w-4 p-0 hover:bg-muted"
          >
            <Star className={cn("h-2.5 w-2.5", isFavorite && "fill-yellow-400 text-yellow-400")} />
          </Button>
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setEditDialogOpen(true)}
            className="h-4 w-4 p-0 hover:bg-muted"
          >
            <Pencil className="h-2.5 w-2.5" />
          </Button>
          <SubagentButton
            context={{ issue_id: issueId }}
            suggestedAgent="issue-triager"
            suggestedPrompt="Analyze this issue and suggest priority, type, tags, and any dependencies."
            size="sm"
          />
          <span className="text-xs text-muted-foreground">•</span>
          <Badge variant="secondary" className={cn("h-4 text-[10px] leading-none capitalize px-1.5 py-0", typeColors[issue.type])}>
            {issue.type}
          </Badge>
          {issue.type === "discovery" ? (
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Badge
                  variant="secondary"
                  className={cn("h-4 text-[10px] leading-none capitalize px-1.5 py-0 cursor-pointer", discoveryStatusColors[issue.discovery_status || "proposed"])}
                >
                  {(issue.discovery_status || "proposed").replace('_', ' ')}
                </Badge>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="start">
                <DropdownMenuRadioGroup
                  value={issue.discovery_status || "proposed"}
                  onValueChange={(value) => {
                    updateIssue.mutate(
                      { id: issue.id, data: { discovery_status: value } },
                      {
                        onSuccess: () => {
                          toast.success("Discovery status updated successfully");
                        },
                        onError: (error) => {
                          toast.error(error instanceof Error ? error.message : "Failed to update discovery status");
                        },
                      }
                    );
                  }}
                >
                  <DropdownMenuRadioItem value="proposed">Proposed</DropdownMenuRadioItem>
                  <DropdownMenuRadioItem value="researching">Researching</DropdownMenuRadioItem>
                  <DropdownMenuRadioItem value="findings_ready">Findings Ready</DropdownMenuRadioItem>
                  <DropdownMenuRadioItem value="approved">Approved</DropdownMenuRadioItem>
                  <DropdownMenuRadioItem value="parked">Parked</DropdownMenuRadioItem>
                  <DropdownMenuRadioItem value="declined">Declined</DropdownMenuRadioItem>
                </DropdownMenuRadioGroup>
              </DropdownMenuContent>
            </DropdownMenu>
          ) : (
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Badge
                  variant="secondary"
                  className={cn("h-4 text-[10px] leading-none capitalize px-1.5 py-0 cursor-pointer", statusColors[issue.status])}
                >
                  {issue.status.replace('_', ' ')}
                </Badge>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="start">
                <DropdownMenuRadioGroup
                  value={issue.status}
                  onValueChange={(value) => {
                    updateIssue.mutate(
                      { id: issue.id, data: { status: value } },
                      {
                        onSuccess: () => {
                          toast.success("Status updated successfully");
                        },
                        onError: (error) => {
                          toast.error(error instanceof Error ? error.message : "Failed to update status");
                        },
                      }
                    );
                  }}
                >
                  <DropdownMenuRadioItem value="open">Open</DropdownMenuRadioItem>
                  <DropdownMenuRadioItem value="ready">Ready</DropdownMenuRadioItem>
                  <DropdownMenuRadioItem value="in_progress">In Progress</DropdownMenuRadioItem>
                  <DropdownMenuRadioItem value="review">Review</DropdownMenuRadioItem>
                  <DropdownMenuRadioItem value="testing">Testing</DropdownMenuRadioItem>
                  <DropdownMenuRadioItem value="closed">Closed</DropdownMenuRadioItem>
                </DropdownMenuRadioGroup>
              </DropdownMenuContent>
            </DropdownMenu>
          )}
          <Badge variant="secondary" className={cn("h-4 text-[10px] leading-none capitalize px-1.5 py-0", priorityColors[issue.priority])}>
            {issue.priority}
          </Badge>
          {issue.assignee && (
            <Badge variant="outline" className="h-4 text-[10px] leading-none px-1.5 py-0">
              {issue.assignee}
            </Badge>
          )}
          <span className="text-xs text-muted-foreground">•</span>
          <span className="text-xs text-muted-foreground">
            Created {formatDistanceToNow(new Date(issue.created_at))} ago
          </span>
          <span className="text-xs text-muted-foreground">•</span>
          <span className="text-xs text-muted-foreground">
            Updated {formatDistanceToNow(new Date(issue.updated_at))} ago
          </span>
        </div>

        <Separator />

        {/* Issue Content */}
        <Card>
          <CardHeader>
            <CardTitle>Description</CardTitle>
          </CardHeader>
          <CardContent>
            <MarkdownRenderer content={issue.description} />
          </CardContent>
        </Card>

        <Separator />

        {/* Tabbed Content */}
        <Tabs defaultValue="dependencies" className="w-full">
          <TabsList className="grid w-full grid-cols-4">
            <TabsTrigger value="dependencies">Dependencies</TabsTrigger>
            <TabsTrigger value="forms">Forms</TabsTrigger>
            <TabsTrigger value="documents">Documents</TabsTrigger>
            <TabsTrigger value="attachments">Attachments</TabsTrigger>
          </TabsList>

          <TabsContent value="dependencies">
            <IssueDependenciesTab
              issueId={issue.id}
              blocking={issue.blocking || []}
              blockedBy={issue.blocked_by || []}
            />
          </TabsContent>

          <TabsContent value="forms">
            <IssueFormsTab issueId={issueId} />
          </TabsContent>

          <TabsContent value="documents">
            <IssueDocumentsTab issueId={issueId} projectId={issue.project_id || ""} />
          </TabsContent>

          <TabsContent value="attachments">
            <IssueAttachmentsTab issueId={issueId} />
          </TabsContent>
        </Tabs>
        </div>

        {/* Collapsible & Resizable Comments Section */}
        <EntityCommentsSection
          entityType="issue"
          entityId={issueId}
          defaultHeight={500}
          minHeight={200}
          maxHeight={800}
        />
      </div>

      {/* Edit Issue Dialog */}
      {issue && (
        <EditIssueDialog
          issue={issue}
          open={editDialogOpen}
          onOpenChange={setEditDialogOpen}
        />
      )}
    </PageLayout>
  );
}
