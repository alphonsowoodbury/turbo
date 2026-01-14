"use client";

import { useChatSidebar } from "@/hooks/use-chat-sidebar";
import { useMentors } from "@/hooks/use-mentors";
import { MentorChat } from "@/components/mentors/mentor-chat";
import { Button } from "@/components/ui/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { X, MessageSquare } from "lucide-react";
import { cn } from "@/lib/utils";

export function ChatSidebar() {
  const { isOpen, activeMentorId, close, setActiveMentor } = useChatSidebar();
  const { data: mentors, isLoading } = useMentors();

  // Don't render if not open
  if (!isOpen) return null;

  // Filter to only active mentors
  const activeMentors = mentors?.filter((m) => m.is_active) || [];

  return (
    <div className="flex flex-col h-full border-l bg-background">
      {/* Header */}
      <div className="flex items-center justify-between gap-2 p-3 border-b bg-muted/30">
        <div className="flex items-center gap-2 flex-1 min-w-0">
          <MessageSquare className="h-4 w-4 text-muted-foreground flex-shrink-0" />
          <Select
            value={activeMentorId || ""}
            onValueChange={(value) => setActiveMentor(value)}
          >
            <SelectTrigger className="h-8 text-sm border-none shadow-none focus:ring-0 flex-1">
              <SelectValue placeholder="Select a mentor..." />
            </SelectTrigger>
            <SelectContent>
              {isLoading ? (
                <SelectItem value="loading" disabled>
                  Loading mentors...
                </SelectItem>
              ) : activeMentors.length === 0 ? (
                <SelectItem value="none" disabled>
                  No active mentors
                </SelectItem>
              ) : (
                activeMentors.map((mentor) => (
                  <SelectItem key={mentor.id} value={mentor.id}>
                    <div className="flex items-center gap-2">
                      <span>{mentor.name}</span>
                      <span className="text-xs text-muted-foreground">
                        ({mentor.workspace})
                      </span>
                    </div>
                  </SelectItem>
                ))
              )}
            </SelectContent>
          </Select>
        </div>
        <Button
          variant="ghost"
          size="sm"
          onClick={close}
          className="h-8 w-8 p-0 flex-shrink-0"
          title="Close chat"
        >
          <X className="h-4 w-4" />
        </Button>
      </div>

      {/* Chat Content */}
      <div className="flex-1 overflow-hidden">
        {activeMentorId ? (
          <MentorChat mentorId={activeMentorId} />
        ) : (
          <div className="flex flex-col items-center justify-center h-full p-6 text-center">
            <MessageSquare className="h-12 w-12 text-muted-foreground/50 mb-4" />
            <h3 className="font-semibold text-sm mb-2">No Mentor Selected</h3>
            <p className="text-xs text-muted-foreground max-w-[250px]">
              Select a mentor from the dropdown above to start a conversation.
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
