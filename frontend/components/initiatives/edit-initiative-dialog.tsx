"use client";

import { useState, useEffect } from "react";
import { useUpdateInitiative } from "@/hooks/use-initiatives";
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
import type { Initiative, InitiativeStatus } from "@/lib/types";

interface EditInitiativeDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  initiative: Initiative;
  projectId?: string | null;
}

export function EditInitiativeDialog({
  open,
  onOpenChange,
  initiative,
  projectId,
}: EditInitiativeDialogProps) {
  const [name, setName] = useState(initiative.name);
  const [description, setDescription] = useState(initiative.description);
  const [status, setStatus] = useState<InitiativeStatus>(initiative.status);
  const [startDate, setStartDate] = useState(
    initiative.start_date ? new Date(initiative.start_date).toISOString().split("T")[0] : ""
  );
  const [targetDate, setTargetDate] = useState(
    initiative.target_date ? new Date(initiative.target_date).toISOString().split("T")[0] : ""
  );
  const [selectedIssueIds, setSelectedIssueIds] = useState<string[]>([]);

  const updateInitiative = useUpdateInitiative();
  // Get all issues (initiatives can span projects or have no project)
  const { data: issues } = useIssues(projectId ? { project_id: projectId } : {});

  // Reset form when initiative changes
  useEffect(() => {
    setName(initiative.name);
    setDescription(initiative.description);
    setStatus(initiative.status);
    setStartDate(
      initiative.start_date ? new Date(initiative.start_date).toISOString().split("T")[0] : ""
    );
    setTargetDate(
      initiative.target_date ? new Date(initiative.target_date).toISOString().split("T")[0] : ""
    );
    setSelectedIssueIds([]);
  }, [initiative]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!name.trim() || !description.trim()) {
      toast.error("Please fill in all required fields");
      return;
    }

    updateInitiative.mutate(
      {
        id: initiative.id,
        data: {
          name: name.trim(),
          description: description.trim(),
          status,
          start_date: startDate || null,
          target_date: targetDate || null,
          issue_ids: selectedIssueIds.length > 0 ? selectedIssueIds : null,
        },
      },
      {
        onSuccess: () => {
          toast.success("Initiative updated successfully!");
          onOpenChange(false);
        },
        onError: (error) => {
          toast.error(
            error instanceof Error ? error.message : "Failed to update initiative"
          );
        },
      }
    );
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[525px] max-h-[90vh] overflow-y-auto">
        <form onSubmit={handleSubmit}>
          <DialogHeader>
            <DialogTitle>Edit Initiative</DialogTitle>
            <DialogDescription>
              Update initiative details and associated issues.
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
                placeholder="Initiative name"
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
                placeholder="Describe the initiative..."
                rows={3}
                required
              />
            </div>

            <div className="grid gap-2">
              <Label htmlFor="status">Status</Label>
              <Select
                value={status}
                onValueChange={(value) => setStatus(value as InitiativeStatus)}
              >
                <SelectTrigger id="status">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="planning">Planning</SelectItem>
                  <SelectItem value="in_progress">In Progress</SelectItem>
                  <SelectItem value="on_hold">On Hold</SelectItem>
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
                <Label htmlFor="targetDate">Target Date</Label>
                <Input
                  id="targetDate"
                  type="date"
                  value={targetDate}
                  onChange={(e) => setTargetDate(e.target.value)}
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
            <Button type="submit" disabled={updateInitiative.isPending}>
              {updateInitiative.isPending ? "Updating..." : "Update Initiative"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
