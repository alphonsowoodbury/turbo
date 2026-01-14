"use client";

import { StaffMessage } from "@/lib/api/staff";
import { User, Shield } from "lucide-react";
import { formatDistanceToNow, format } from "date-fns";
import ReactMarkdown from "react-markdown";
import { cn } from "@/lib/utils";

interface StaffMessageBubbleProps {
  message: StaffMessage;
  staffId: string;
}

export function StaffMessageBubble({ message, staffId }: StaffMessageBubbleProps) {
  const isUser = message.message_type === "user";
  const isAssistant = message.message_type === "assistant";

  return (
    <div
      className={cn(
        "flex gap-3 mb-4 group",
        isUser ? "flex-row-reverse" : "flex-row"
      )}
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
          <Shield className="h-5 w-5 text-white" />
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
          {isAssistant ? (
            <div className="prose prose-sm dark:prose-invert max-w-none">
              <ReactMarkdown>{message.content}</ReactMarkdown>
            </div>
          ) : (
            <p className="whitespace-pre-wrap break-words">{message.content}</p>
          )}
        </div>

        {/* Timestamp */}
        <span
          className="text-xs text-muted-foreground mt-1"
          title={format(new Date(message.created_at), "PPpp")}
        >
          {format(new Date(message.created_at), "h:mm a")} · {formatDistanceToNow(new Date(message.created_at), {
            addSuffix: true,
          })}
        </span>
      </div>
    </div>
  );
}
