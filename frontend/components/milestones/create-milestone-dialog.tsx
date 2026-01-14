"use client";

import { useState } from "react";
import { useCreateMilestone } from "@/hooks/use-milestones";
import { useIssues } from "@/hooks/use-issues";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Checkbox } from "@/components/ui/checkbox";
import { ScrollArea } from "@/components/ui/scroll-area";
import { toast } from "sonner";
import type { MilestoneStatus } from "@/lib/types";

interface CreateMilestoneDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  projectId: string;
}

export function CreateMilestoneDialog({
  open,
  onOpenChange,
  projectId,
}: CreateMilestoneDialogProps) {
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [status, setStatus] = useState<MilestoneStatus>("planned");
  const [startDate, setStartDate] = useState("");
  const [dueDate, setDueDate] = useState("");
  const [selectedIssueIds, setSelectedIssueIds] = useState<string[]>([]);

  const createMilestone = useCreateMilestone();
  const { data: issues } = useIssues({ project_id: projectId });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!name.trim() || !description.trim() || !dueDate) {
      toast.error("Please fill in all required fields");
      return;
    }

    createMilestone.mutate(
      {
        name: name.trim(),
        description: description.trim(),
        status,
        start_date: startDate || null,
        due_date: dueDate,
        project_id: projectId,
        issue_ids: selectedIssueIds.length > 0 ? selectedIssueIds : null,
      },
      {
        onSuccess: () => {
          toast.success("Milestone created successfully!");
          setName("");
          setDescription("");
          setStatus("planned");
          setStartDate("");
          setDueDate("");
          setSelectedIssueIds([]);
          onOpenChange(false);
        },
        onError: (error) => {
          toast.error(
            error instanceof Error ? error.message : "Failed to create milestone"
          );
        },
      }
    );
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[525px]">
        <form onSubmit={handleSubmit}>
          <DialogHeader>
            <DialogTitle>Create New Milestone</DialogTitle>
            <DialogDescription>
              Add a new milestone to track project progress.
            </DialogDescription>
          </DialogHeader>

          <div className="grid gap-4 py-4">
            <div className="grid gap-2">
              <Label htmlFor="name">
                Name <span className="text-destructive">*</span>
              </Label>
              <Input
                id="name"
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="Milestone name"
                required
              />
            </div>

            <div className="grid gap-2">
              <Label htmlFor="description">
                Description <span className="text-destructive">*</span>
              </Label>
              <Textarea
                id="description"
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                placeholder="Describe the milestone..."
                rows={3}
                required
              />
            </div>

            <div className="grid gap-2">
              <Label htmlFor="status">Status</Label>
              <Select
                value={status}
                onValueChange={(value) => setStatus(value as MilestoneStatus)}
              >
                <SelectTrigger id="status">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="planned">Planned</SelectItem>
                  <SelectItem value="in_progress">In Progress</SelectItem>
                  <SelectItem value="completed">Completed</SelectItem>
                  <SelectItem value="cancelled">Cancelled</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="grid gap-2">
                <Label htmlFor="startDate">Start Date</Label>
                <Input
                  id="startDate"
                  type="date"
                  value={startDate}
                  onChange={(e) => setStartDate(e.target.value)}
                />
              </div>

              <div className="grid gap-2">
                <Label htmlFor="dueDate">
                  Due Date <span className="text-destructive">*</span>
                </Label>
                <Input
                  id="dueDate"
                  type="date"
                  value={dueDate}
                  onChange={(e) => setDueDate(e.target.value)}
                  required
                />
              </div>
            </div>

            {issues && issues.length > 0 && (
              <div className="grid gap-2">
                <Label>Issues (Optional)</Label>
                <div className="border rounded-lg p-3">
                  <ScrollArea className="h-48">
                    <div className="space-y-2">
                      {issues.map((issue) => (
                        <div key={issue.id} className="flex items-start space-x-2">
                          <Checkbox
                            id={`issue-${issue.id}`}
                            checked={selectedIssueIds.includes(issue.id)}
                            onCheckedChange={(checked) => {
                              if (checked) {
                                setSelectedIssueIds([...selectedIssueIds, issue.id]);
                              } else {
                                setSelectedIssueIds(
                                  selectedIssueIds.filter((id) => id !== issue.id)
                                );
                              }
                            }}
                          />
                          <label
                            htmlFor={`issue-${issue.id}`}
                            className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70 cursor-pointer"
                          >
                            {issue.title}
                            <span className="ml-2 text-xs text-muted-foreground">
                              ({issue.status})
                            </span>
                          </label>
                        </div>
                      ))}
                    </div>
                  </ScrollArea>
                  {selectedIssueIds.length > 0 && (
                    <p className="text-xs text-muted-foreground mt-2">
                      {selectedIssueIds.length} issue{selectedIssueIds.length > 1 ? "s" : ""} selected
                    </p>
                  )}
                </div>
              </div>
            )}
          </div>

          <DialogFooter>
            <Button
              type="button"
              variant="outline"
              onClick={() => onOpenChange(false)}
            >
              Cancel
            </Button>
            <Button type="submit" disabled={createMilestone.isPending}>
              {createMilestone.isPending ? "Creating..." : "Create Milestone"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}