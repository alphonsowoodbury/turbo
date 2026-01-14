"use client";

import { useState, useEffect } from "react";
import { useUpdateIssue } from "@/hooks/use-issues";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Loader2, Eye } from "lucide-react";
import { toast } from "sonner";
import dynamic from "next/dynamic";
import { MarkdownRenderer } from "@/components/ui/markdown-renderer";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";

// Dynamically import MD Editor to avoid SSR issues
const MDEditor = dynamic(() => import("@uiw/react-md-editor"), {
  ssr: false,
  loading: () => <div className="h-64 animate-pulse bg-muted rounded-md" />,
});

interface Issue {
  id: string;
  title: string;
  description: string;
  type: "feature" | "bug" | "task" | "enhancement" | "documentation" | "discovery";
  status: "open" | "in_progress" | "review" | "testing" | "closed";
  priority: "low" | "medium" | "high" | "critical";
  assignee?: string;
  project_id: string;
}

interface EditIssueDialogProps {
  issue: Issue;
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function EditIssueDialog({ issue, open, onOpenChange }: EditIssueDialogProps) {
  const [title, setTitle] = useState(issue.title);
  const [description, setDescription] = useState(issue.description);
  const [type, setType] = useState(issue.type);
  const [status, setStatus] = useState(issue.status);
  const [priority, setPriority] = useState(issue.priority);
  const [assignee, setAssignee] = useState(issue.assignee || "");
  const [previewMode, setPreviewMode] = useState<"edit" | "preview">("edit");

  const updateIssue = useUpdateIssue();

  // Reset form when dialog opens with new issue data
  useEffect(() => {
    if (open) {
      setTitle(issue.title);
      setDescription(issue.description);
      setType(issue.type);
      setStatus(issue.status);
      setPriority(issue.priority);
      setAssignee(issue.assignee || "");
      setPreviewMode("edit");
    }
  }, [open, issue]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();

    if (!title.trim()) {
      toast.error("Title is required");
      return;
    }

    if (!description.trim()) {
      toast.error("Description is required");
      return;
    }

    const updateData: any = {};

    if (title !== issue.title) updateData.title = title;
    if (description !== issue.description) updateData.description = description;
    if (type !== issue.type) updateData.type = type;
    if (status !== issue.status) updateData.status = status;
    if (priority !== issue.priority) updateData.priority = priority;
    if (assignee !== (issue.assignee || "")) {
      updateData.assignee = assignee || null;
    }

    if (Object.keys(updateData).length === 0) {
      toast.info("No changes to save");
      onOpenChange(false);
      return;
    }

    updateIssue.mutate(
      { id: issue.id, data: updateData },
      {
        onSuccess: () => {
          toast.success("Issue updated successfully");
          onOpenChange(false);
        },
        onError: (error) => {
          toast.error(error instanceof Error ? error.message : "Failed to update issue");
        },
      }
    );
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>Edit Issue</DialogTitle>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Title */}
          <div className="space-y-2">
            <Label htmlFor="title">Title</Label>
            <Input
              id="title"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="Issue title"
              required
            />
          </div>

          {/* Description with Markdown Editor */}
          <div className="space-y-2">
            <Label htmlFor="description">Description</Label>
            <Tabs value={previewMode} onValueChange={(v) => setPreviewMode(v as "edit" | "preview")}>
              <TabsList className="grid w-full grid-cols-2">
                <TabsTrigger value="edit">Edit</TabsTrigger>
                <TabsTrigger value="preview">Preview</TabsTrigger>
              </TabsList>
              <TabsContent value="edit" className="mt-2">
                <div data-color-mode="light">
                  <MDEditor
                    value={description}
                    onChange={(val) => setDescription(val || "")}
                    preview="edit"
                    height={300}
                    visibleDragbar={false}
                  />
                </div>
              </TabsContent>
              <TabsContent value="preview" className="mt-2">
                <div className="min-h-[300px] rounded-md border border-border p-4 bg-muted/50">
                  {description ? (
                    <MarkdownRenderer content={description} />
                  ) : (
                    <p className="text-sm text-muted-foreground italic">No description yet</p>
                  )}
                </div>
              </TabsContent>
            </Tabs>
          </div>

          {/* Row 1: Type and Status */}
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="type">Type</Label>
              <Select value={type} onValueChange={(v: any) => setType(v)}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="feature">Feature</SelectItem>
                  <SelectItem value="bug">Bug</SelectItem>
                  <SelectItem value="task">Task</SelectItem>
                  <SelectItem value="enhancement">Enhancement</SelectItem>
                  <SelectItem value="documentation">Documentation</SelectItem>
                  <SelectItem value="discovery">Discovery</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label htmlFor="status">Status</Label>
              <Select value={status} onValueChange={(v: any) => setStatus(v)}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="open">Open</SelectItem>
                  <SelectItem value="ready">Ready</SelectItem>
                  <SelectItem value="in_progress">In Progress</SelectItem>
                  <SelectItem value="review">Review</SelectItem>
                  <SelectItem value="testing">Testing</SelectItem>
                  <SelectItem value="closed">Closed</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>

          {/* Row 2: Priority and Assignee */}
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="priority">Priority</Label>
              <Select value={priority} onValueChange={(v: any) => setPriority(v)}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="low">Low</SelectItem>
                  <SelectItem value="medium">Medium</SelectItem>
                  <SelectItem value="high">High</SelectItem>
                  <SelectItem value="critical">Critical</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label htmlFor="assignee">Assignee (Email)</Label>
              <Input
                id="assignee"
                type="email"
                value={assignee}
                onChange={(e) => setAssignee(e.target.value)}
                placeholder="user@example.com"
              />
            </div>
          </div>

          <DialogFooter>
            <Button
              type="button"
              variant="outline"
              onClick={() => onOpenChange(false)}
              disabled={updateIssue.isPending}
            >
              Cancel
            </Button>
            <Button type="submit" disabled={updateIssue.isPending}>
              {updateIssue.isPending && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
              Save Changes
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}