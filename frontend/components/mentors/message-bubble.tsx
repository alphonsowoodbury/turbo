"use client";

import { useState } from "react";
import { MentorMessage } from "@/lib/api/mentors";
import { User, Bot, Edit2, Check, X } from "lucide-react";
import { formatDistanceToNow, format } from "date-fns";
import ReactMarkdown from "react-markdown";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { useUpdateMessage } from "@/hooks/use-mentor-messages";
import { toast } from "sonner";

interface MessageBubbleProps {
  message: MentorMessage;
  mentorId: string;
}

export function MessageBubble({ message, mentorId }: MessageBubbleProps) {
  const isUser = message.role === "user";
  const isAssistant = message.role === "assistant";
  const [isEditing, setIsEditing] = useState(false);
  const [editedContent, setEditedContent] = useState(message.content);
  const [isHovered, setIsHovered] = useState(false);

  const updateMessageMutation = useUpdateMessage();

  const handleStartEdit = () => {
    setEditedContent(message.content);
    setIsEditing(true);
  };

  const handleCancelEdit = () => {
    setEditedContent(message.content);
    setIsEditing(false);
  };

  const handleSaveEdit = async () => {
    if (!editedContent.trim() || editedContent === message.content) {
      setIsEditing(false);
      return;
    }

    try {
      await updateMessageMutation.mutateAsync({
        mentorId,
        messageId: message.id,
        content: editedContent.trim(),
      });
      setIsEditing(false);
      toast.success("Message Updated", {
        description: "Your message has been updated successfully.",
      });
    } catch (error) {
      toast.error("Error", {
        description: "Failed to update message. Please try again.",
      });
    }
  };

  return (
    <div
      className={cn(
        "flex gap-3 mb-4 group",
        isUser ? "flex-row-reverse" : "flex-row"
      )}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
    >
      {/* Avatar */}
      <div
        className={cn(
          "flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center",
          isUser ? "bg-blue-500" : "bg-purple-500"
        )}
      >
        {isUser ? (
          <User className="h-5 w-5 text-white" />
        ) : (
          <Bot className="h-5 w-5 text-white" />
        )}
      </div>

      {/* Message Content */}
      <div
        className={cn(
          "flex flex-col max-w-[70%]",
          isUser ? "items-end" : "items-start"
        )}
      >
        {/* Message Bubble */}
        <div
          className={cn(
            "rounded-lg px-4 py-2 shadow-sm relative",
            isUser
              ? "bg-blue-500 text-white"
              : "bg-secondary text-secondary-foreground"
          )}
        >
          {isEditing ? (
            <div className="space-y-2">
              <Textarea
                value={editedContent}
                onChange={(e) => setEditedContent(e.target.value)}
                className={cn(
                  "min-h-[60px] text-sm resize-none",
                  isUser
                    ? "bg-blue-600 text-white border-blue-400 placeholder:text-blue-200"
                    : "bg-background"
                )}
                autoFocus
              />
              <div className="flex gap-2 justify-end">
                <Button
                  size="sm"
                  variant="ghost"
                  onClick={handleCancelEdit}
                  className={cn(
                    "h-7 px-2 text-xs",
                    isUser && "text-white hover:bg-blue-600"
                  )}
                >
                  <X className="h-3 w-3 mr-1" />
                  Cancel
                </Button>
                <Button
                  size="sm"
                  onClick={handleSaveEdit}
                  disabled={updateMessageMutation.isPending}
                  className={cn(
                    "h-7 px-2 text-xs",
                    isUser && "bg-blue-600 hover:bg-blue-700"
                  )}
                >
                  <Check className="h-3 w-3 mr-1" />
                  Save
                </Button>
              </div>
            </div>
          ) : (
            <>
              {isAssistant ? (
                <div className="prose prose-sm dark:prose-invert max-w-none">
                  <ReactMarkdown>{message.content}</ReactMarkdown>
                </div>
              ) : (
                <p className="whitespace-pre-wrap break-words">{message.content}</p>
              )}
              {/* Edit Button - Only show for user messages on hover */}
              {isUser && isHovered && !isEditing && (
                <Button
                  size="sm"
                  variant="ghost"
                  onClick={handleStartEdit}
                  className="absolute -top-2 -right-2 h-6 w-6 p-0 bg-white text-gray-700 hover:bg-gray-100 rounded-full shadow-sm opacity-0 group-hover:opacity-100 transition-opacity"
                  title="Edit message"
                >
                  <Edit2 className="h-3 w-3" />
                </Button>
              )}
            </>
          )}
        </div>

        {/* Timestamp */}
        {!isEditing && (
          <span
            className="text-xs text-muted-foreground mt-1"
            title={format(new Date(message.created_at), "PPpp")}
          >
            {format(new Date(message.created_at), "h:mm a")} · {formatDistanceToNow(new Date(message.created_at), {
              addSuffix: true,
            })}
          </span>
        )}
      </div>
    </div>
  );
}
