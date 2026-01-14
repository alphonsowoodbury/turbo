"use client";

import { useEffect, useRef, useState } from "react";
import { MessageBubble } from "./message-bubble";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Card } from "@/components/ui/card";
import { Loader2, Send, Trash2, Zap } from "lucide-react";
import { useMentorMessages, useSendMessage, useClearConversation } from "@/hooks/use-mentor-messages";
import { useMentorStreaming } from "@/hooks/use-mentor-streaming";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { toast } from "sonner";

interface MentorChatProps {
  mentorId: string;
  messagesOnly?: boolean; // If true, only show messages (no input)
  inputOnly?: boolean; // If true, only show input (no messages)
  enableStreaming?: boolean; // If true, use real-time streaming instead of webhook
}

export function MentorChat({ mentorId, messagesOnly = false, inputOnly = false, enableStreaming = true }: MentorChatProps) {
  const [message, setMessage] = useState("");
  const [clearDialogOpen, setClearDialogOpen] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Fetch conversation history
  const { data: conversation, isLoading, error } = useMentorMessages(mentorId);

  // Send message mutation (webhook-based)
  const sendMessageMutation = useSendMessage();

  // Streaming hook (SSE-based)
  const {
    sendMessage: sendStreamingMessage,
    isStreaming,
    streamingContent,
    error: streamingError,
    abortStream
  } = useMentorStreaming(mentorId);

  // Clear conversation mutation
  const clearConversationMutation = useClearConversation();

  // Auto-scroll to bottom when messages change
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [conversation?.messages]);

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
  }, [message]);

  const handleSendMessage = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!message.trim() || sendMessageMutation.isPending || isStreaming) return;

    const messageContent = message.trim();
    setMessage(""); // Clear input immediately for better UX

    // Reset textarea height
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
    }

    try {
      if (enableStreaming) {
        // Use streaming endpoint
        await sendStreamingMessage(messageContent);

        if (!streamingError) {
          toast.success("Message Sent", {
            description: "Response received in real-time.",
          });
        }
      } else {
        // Use webhook endpoint (original behavior)
        const response = await sendMessageMutation.mutateAsync({
          mentorId,
          content: messageContent,
        });

        if (response.status === "error") {
          toast.error("Error", {
            description: response.error || "Failed to send message",
          });
        } else if (response.status === "pending") {
          toast.info("Processing", {
            description: "Your message is being processed. The response may take a moment.",
          });
        }
      }
    } catch (error) {
      toast.error("Error", {
        description: "Failed to send message. Please try again.",
      });
      setMessage(messageContent); // Restore message on error
    }
  };

  const handleClearConversation = async () => {
    try {
      await clearConversationMutation.mutateAsync(mentorId);
      setClearDialogOpen(false);
      toast.success("Conversation Cleared", {
        description: "All messages have been deleted.",
      });
    } catch (error) {
      toast.error("Error", {
        description: "Failed to clear conversation. Please try again.",
      });
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    // Submit on Enter (without Shift)
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage(e as any);
    }
  };

  if (error) {
    return (
      <Card className="p-6 text-center">
        <p className="text-destructive">Failed to load conversation. Please try again.</p>
      </Card>
    );
  }

  // Render only input (for fixed bottom section)
  if (inputOnly) {
    return (
      <form onSubmit={handleSendMessage}>
        <div className="flex gap-2 items-end">
          <Textarea
            ref={textareaRef}
            placeholder="Send a message... (Enter to send, Shift+Enter for new line)"
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            onKeyDown={handleKeyDown}
            rows={1}
            disabled={sendMessageMutation.isPending}
            className="min-h-[36px] max-h-[200px] text-sm resize-none"
          />
          <Button
            type="submit"
            size="sm"
            disabled={!message.trim() || sendMessageMutation.isPending}
            className="h-9 w-9 p-0 flex-shrink-0"
          >
            {sendMessageMutation.isPending ? (
              <Loader2 className="h-3.5 w-3.5 animate-spin" />
            ) : (
              <Send className="h-3.5 w-3.5" />
            )}
          </Button>
        </div>
      </form>
    );
  }

  return (
    <div className="flex flex-col h-full">
      {/* Header with Clear Button - Only show if not messagesOnly */}
      {!messagesOnly && (
        <div className="flex justify-end mb-4">
          <Dialog open={clearDialogOpen} onOpenChange={setClearDialogOpen}>
            <DialogTrigger asChild>
              <Button
                variant="outline"
                size="sm"
                disabled={!conversation?.messages?.length || clearConversationMutation.isPending}
              >
                <Trash2 className="h-4 w-4 mr-2" />
                Clear Conversation
              </Button>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>Clear Conversation</DialogTitle>
                <DialogDescription>
                  This will permanently delete all messages in this conversation. This action cannot be undone.
                </DialogDescription>
              </DialogHeader>
              <DialogFooter>
                <Button variant="outline" onClick={() => setClearDialogOpen(false)}>
                  Cancel
                </Button>
                <Button variant="destructive" onClick={handleClearConversation}>
                  Clear
                </Button>
              </DialogFooter>
            </DialogContent>
          </Dialog>
        </div>
      )}

      {/* Scrollable Messages List - Compact */}
      <div className="flex-1 overflow-y-auto px-4 py-3 space-y-2">
        {isLoading ? (
          <div className="flex items-center justify-center h-32">
            <div className="text-sm text-muted-foreground">Loading messages...</div>
          </div>
        ) : conversation?.messages?.length === 0 && !isStreaming ? (
          <div className="flex items-center justify-center h-32">
            <div className="text-center text-muted-foreground">
              <p className="text-sm font-medium">No messages yet</p>
              <p className="text-xs mt-1">Start a conversation with your mentor</p>
            </div>
          </div>
        ) : (
          <>
            {conversation?.messages?.map((msg) => (
              <MessageBubble key={msg.id} message={msg} mentorId={mentorId} />
            ))}

            {/* Show streaming message while it's being generated or until saved */}
            {streamingContent && (
              <div className="flex justify-start">
                <div className="relative max-w-[85%] rounded-lg px-3 py-2 text-xs bg-muted">
                  <div className="flex items-start gap-2">
                    <Zap className={`h-3 w-3 mt-0.5 text-blue-500 flex-shrink-0 ${isStreaming ? 'animate-pulse' : ''}`} />
                    <div className="whitespace-pre-wrap break-words">
                      {streamingContent}
                      {isStreaming && <span className="inline-block w-1 h-3 ml-0.5 bg-current animate-pulse" />}
                    </div>
                  </div>
                </div>
              </div>
            )}

            <div ref={messagesEndRef} />
          </>
        )}
      </div>

      {/* Fixed Message Input at Bottom - Only show if not messagesOnly */}
      {!messagesOnly && (
        <div className="flex-shrink-0 border-t bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
          <form onSubmit={handleSendMessage} className="p-3">
            <div className="flex gap-2 items-end">
              <Textarea
                ref={textareaRef}
                placeholder="Send a message... (Enter to send, Shift+Enter for new line)"
                value={message}
                onChange={(e) => setMessage(e.target.value)}
                onKeyDown={handleKeyDown}
                rows={1}
                disabled={sendMessageMutation.isPending}
                className="min-h-[36px] max-h-[200px] text-xs resize-none"
              />
              <Button
                type="submit"
                size="sm"
                disabled={!message.trim() || sendMessageMutation.isPending || isStreaming}
                className="h-9 w-9 p-0 flex-shrink-0"
                title={enableStreaming ? "Send with real-time streaming" : "Send message"}
              >
                {(sendMessageMutation.isPending || isStreaming) ? (
                  <Loader2 className="h-3.5 w-3.5 animate-spin" />
                ) : enableStreaming ? (
                  <Zap className="h-3.5 w-3.5" />
                ) : (
                  <Send className="h-3.5 w-3.5" />
                )}
              </Button>
            </div>
          </form>
        </div>
      )}
    </div>
  );
}
