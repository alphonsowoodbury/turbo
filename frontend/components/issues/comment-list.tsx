"use client";

import { useState, useRef, useEffect } from "react";
import { formatDistanceToNow } from "date-fns";
import { Card, CardContent } from "@/components/ui/card";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Button } from "@/components/ui/button";
import { MentionTextarea } from "@/components/ui/mention-textarea";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Badge } from "@/components/ui/badge";
import { MarkdownRenderer } from "@/components/ui/markdown-renderer";
import { TypingIndicator } from "@/components/ui/typing-indicator";
import { Bot, MoreVertical, Pencil, Trash2, Send, Wifi, WifiOff } from "lucide-react";
import { useComments, useCreateComment, useDeleteComment, useUpdateComment } from "@/hooks/use-comments";
import { useWebSocket } from "@/hooks/use-websocket";
import { cn } from "@/lib/utils";
import { toast } from "sonner";
import type { Comment, EntityType } from "@/lib/types";

interface CommentListProps {
  entityType: EntityType;
  entityId: string;
}

export function CommentList({ entityType, entityId }: CommentListProps) {
  const { data: comments, isLoading } = useComments(entityType, entityId);
  const createComment = useCreateComment();
  const updateComment = useUpdateComment();
  const deleteComment = useDeleteComment();

  // WebSocket connection for real-time updates
  const { isConnected, isTyping, typingAuthor } = useWebSocket({
    entityType,
    entityId,
    enabled: !!entityType && !!entityId,
    onMessage: (message) => {
      // Optional: Show toast notifications for new comments from others
      if (message.type === "comment_created" && message.data.author_type === "ai") {
        toast.info("Claude added a comment");
      }
    },
  });

  const [newComment, setNewComment] = useState("");
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editContent, setEditContent] = useState("");
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Auto-resize textarea as user types
  const adjustTextareaHeight = () => {
    const textarea = textareaRef.current;
    if (textarea) {
      textarea.style.height = "auto";
      textarea.style.height = `${Math.min(textarea.scrollHeight, 200)}px`;
    }
  };

  useEffect(() => {
    adjustTextareaHeight();
  }, [newComment]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newComment.trim()) return;

    createComment.mutate(
      {
        entity_type: entityType,
        entity_id: entityId,
        content: newComment.trim(),
        author_name: "Current User", // TODO: Get from auth
        author_type: "user",
      },
      {
        onSuccess: () => {
          setNewComment("");
          toast.success("Comment added");
          // Reset textarea height
          if (textareaRef.current) {
            textareaRef.current.style.height = "auto";
          }
        },
        onError: (error) => {
          toast.error(error instanceof Error ? error.message : "Failed to add comment");
        },
      }
    );
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    // Submit on Enter (without Shift)
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e as any);
    }
  };

  const handleEdit = (comment: Comment) => {
    setEditingId(comment.id);
    setEditContent(comment.content);
  };

  const handleUpdate = (commentId: string) => {
    if (!editContent.trim()) return;

    updateComment.mutate(
      {
        id: commentId,
        data: { content: editContent.trim() },
      },
      {
        onSuccess: () => {
          setEditingId(null);
          setEditContent("");
          toast.success("Comment updated");
        },
        onError: (error) => {
          toast.error(error instanceof Error ? error.message : "Failed to update comment");
        },
      }
    );
  };

  const handleDelete = (commentId: string) => {
    if (!confirm("Are you sure you want to delete this comment?")) return;

    deleteComment.mutate(
      { id: commentId, entityType, entityId },
      {
        onSuccess: () => {
          toast.success("Comment deleted");
        },
        onError: (error) => {
          toast.error(error instanceof Error ? error.message : "Failed to delete comment");
        },
      }
    );
  };

  const getInitials = (name: string) => {
    return name
      .split(" ")
      .map((n) => n[0])
      .join("")
      .toUpperCase()
      .slice(0, 2);
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-32">
        <div className="text-sm text-muted-foreground">Loading comments...</div>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full">
      {/* Connection Status Indicator */}
      <div className="px-4 py-1 border-b bg-muted/30">
        <div className="flex items-center gap-1.5 text-xs">
          {isConnected ? (
            <>
              <Wifi className="h-3 w-3 text-green-500" />
              <span className="text-muted-foreground">Live updates enabled</span>
            </>
          ) : (
            <>
              <WifiOff className="h-3 w-3 text-amber-500" />
              <span className="text-muted-foreground">Connecting...</span>
            </>
          )}
        </div>
      </div>

      {/* Scrollable Comments List - Compact */}
      <div className="flex-1 overflow-y-auto px-4 py-3 space-y-2">
        {comments && comments.length > 0 ? (
          <>
            {comments.map((comment) => (
            <Card key={comment.id} className="shadow-none">
              <CardContent className="p-3">
                <div className="flex gap-2">
                  <Avatar className="h-6 w-6 mt-0.5 flex-shrink-0">
                    <AvatarFallback
                      className={cn(
                        "text-xs",
                        comment.author_type === "ai"
                          ? "bg-purple-500/10 text-purple-500"
                          : "bg-primary/10 text-primary"
                      )}
                    >
                      {comment.author_type === "ai" ? (
                        <Bot className="h-3 w-3" />
                      ) : (
                        getInitials(comment.author_name)
                      )}
                    </AvatarFallback>
                  </Avatar>

                  <div className="flex-1 min-w-0 space-y-1">
                    <div className="flex items-center justify-between gap-2">
                      <div className="flex items-center gap-1.5 flex-wrap">
                        <span className="text-xs font-medium">{comment.author_name}</span>
                        {comment.author_type === "ai" && (
                          <Badge variant="secondary" className="text-[9px] h-3.5 px-1 bg-purple-500/10 text-purple-500">
                            AI
                          </Badge>
                        )}
                        <span className="text-[10px] text-muted-foreground">
                          {formatDistanceToNow(new Date(comment.created_at))} ago
                        </span>
                      </div>

                      {comment.author_type === "user" && (
                        <DropdownMenu>
                          <DropdownMenuTrigger asChild>
                            <Button variant="ghost" size="icon" className="h-5 w-5 flex-shrink-0">
                              <MoreVertical className="h-3 w-3" />
                            </Button>
                          </DropdownMenuTrigger>
                          <DropdownMenuContent align="end">
                            <DropdownMenuItem onClick={() => handleEdit(comment)}>
                              <Pencil className="mr-2 h-3 w-3" />
                              Edit
                            </DropdownMenuItem>
                            <DropdownMenuItem
                              onClick={() => handleDelete(comment.id)}
                              className="text-destructive"
                            >
                              <Trash2 className="mr-2 h-3 w-3" />
                              Delete
                            </DropdownMenuItem>
                          </DropdownMenuContent>
                        </DropdownMenu>
                      )}
                    </div>

                    {editingId === comment.id ? (
                      <div className="space-y-1.5">
                        <MentionTextarea
                          value={editContent}
                          onChange={(e) => setEditContent(e.target.value)}
                          rows={2}
                          className="min-h-0 text-xs"
                        />
                        <div className="flex gap-1.5">
                          <Button size="sm" onClick={() => handleUpdate(comment.id)} className="h-7 text-xs">
                            Save
                          </Button>
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => {
                              setEditingId(null);
                              setEditContent("");
                            }}
                            className="h-7 text-xs"
                          >
                            Cancel
                          </Button>
                        </div>
                      </div>
                    ) : (
                      <div className="text-xs prose prose-sm max-w-none dark:prose-invert">
                        <MarkdownRenderer content={comment.content} />
                      </div>
                    )}
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}

          {/* Show typing indicator when AI is thinking */}
          {isTyping && <TypingIndicator authorName={typingAuthor} />}
          </>
        ) : isTyping ? (
          // Show only typing indicator if no comments yet
          <TypingIndicator authorName={typingAuthor} />
        ) : (
          <div className="flex items-center justify-center h-24">
            <p className="text-xs text-muted-foreground">No comments yet. Be the first to comment!</p>
          </div>
        )}
      </div>

      {/* Fixed Comment Input at Bottom - Slim */}
      <div className="border-t bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
        <form onSubmit={handleSubmit} className="p-3">
          <div className="flex gap-2 items-end">
            <MentionTextarea
              ref={textareaRef}
              placeholder="Add a comment... (type @ to mention staff, Enter to send, Shift+Enter for new line)"
              value={newComment}
              onChange={(e) => setNewComment(e.target.value)}
              onKeyDown={handleKeyDown}
              rows={1}
              className="min-h-[36px] max-h-[200px] text-xs resize-none"
            />
            <Button
              type="submit"
              size="sm"
              disabled={!newComment.trim() || createComment.isPending}
              className="h-9 w-9 p-0 flex-shrink-0"
            >
              <Send className="h-3.5 w-3.5" />
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
}
