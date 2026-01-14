"use client";

import { useState } from "react";
import { useStaff, useUpdateStaff } from "@/hooks/use-staff";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import { ScrollArea, ScrollBar } from "@/components/ui/scroll-area";
import { Loader2 } from "lucide-react";
import { toast } from "sonner";

interface ToolsManagementModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

// Available tools (from webhook server)
const AVAILABLE_TOOLS = [
  "list_projects",
  "get_project",
  "get_project_issues",
  "update_project",
  "list_issues",
  "get_issue",
  "create_issue",
  "update_issue",
  "list_milestones",
  "get_milestone",
  "create_milestone",
  "update_milestone",
  "link_issue_to_milestone",
  "unlink_issue_from_milestone",
  "list_initiatives",
  "get_initiative",
  "create_initiative",
  "update_initiative",
  "link_issue_to_initiative",
  "unlink_issue_from_initiative",
  "add_comment",
  "get_entity_comments",
  "list_tags",
  "create_tag",
  "add_tag_to_entity",
  "remove_tag_from_entity",
  "add_blocker",
  "remove_blocker",
  "get_blocking_issues",
  "get_blocked_issues",
  "list_documents",
  "get_document",
  "create_document",
  "update_document",
  "search_documents",
  "web_search",
];

export function ToolsManagementModal({ open, onOpenChange }: ToolsManagementModalProps) {
  const { data: staff, isLoading } = useStaff({ is_active: true });
  const updateStaff = useUpdateStaff();

  const handleToolToggle = async (staffId: string, toolName: string, currentTools: string[]) => {
    const isEnabled = currentTools.includes(toolName);
    const newTools = isEnabled
      ? currentTools.filter((t) => t !== toolName)
      : [...currentTools, toolName];

    try {
      await updateStaff.mutateAsync({
        staffId: staffId,
        data: {
          allowed_tools: newTools,
        },
      });
      toast.success(
        isEnabled
          ? `Removed ${toolName} from staff member`
          : `Added ${toolName} to staff member`
      );
    } catch (error) {
      toast.error("Failed to update staff tools");
      console.error(error);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-[90vw] w-full max-h-[80vh]">
        <DialogHeader>
          <DialogTitle>Manage Staff Tools</DialogTitle>
          <DialogDescription>
            Enable or disable tools for each staff member. Checked tools are available.
          </DialogDescription>
        </DialogHeader>

        {isLoading ? (
          <div className="flex h-64 items-center justify-center">
            <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
          </div>
        ) : (
          <ScrollArea className="w-full h-[60vh]">
            <div className="relative">
              <table className="w-full border-collapse">
                <thead className="sticky top-0 bg-background z-10 border-b">
                  <tr>
                    <th className="sticky left-0 bg-background text-left p-3 font-semibold border-r min-w-[200px]">
                      Tool
                    </th>
                    {staff?.map((member) => (
                      <th
                        key={member.id}
                        className="p-3 text-center font-semibold min-w-[120px] border-r"
                      >
                        <div className="flex flex-col items-center gap-1">
                          <span className="text-sm">{member.name}</span>
                          <span className="text-xs text-muted-foreground">@{member.handle}</span>
                        </div>
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {AVAILABLE_TOOLS.map((tool) => (
                    <tr key={tool} className="border-b hover:bg-muted/50">
                      <td className="sticky left-0 bg-background p-3 font-mono text-sm border-r">
                        {tool}
                      </td>
                      {staff?.map((member) => {
                        const allowedTools = (member.allowed_tools || []) as string[];
                        const isEnabled = allowedTools.includes(tool);

                        return (
                          <td key={member.id} className="p-3 text-center border-r">
                            <div className="flex items-center justify-center">
                              <Checkbox
                                checked={isEnabled}
                                onCheckedChange={() =>
                                  handleToolToggle(member.id, tool, allowedTools)
                                }
                                disabled={updateStaff.isPending}
                              />
                            </div>
                          </td>
                        );
                      })}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <ScrollBar orientation="horizontal" />
            <ScrollBar orientation="vertical" />
          </ScrollArea>
        )}

        <div className="flex justify-end">
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            Close
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  );
}
