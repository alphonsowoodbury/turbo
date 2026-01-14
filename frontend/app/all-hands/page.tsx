"use client";

import { useState, useEffect } from "react";
import { PageLayout } from "@/components/layout/page-layout";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Send, Users } from "lucide-react";
import { formatDistanceToNow } from "date-fns";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8001";

interface StaffMember {
  id: string;
  name: string;
  handle: string;
  role_type: string;
}

interface Message {
  id: string;
  staff_id: string | null;
  message_type: "user" | "assistant";
  content: string;
  created_at: string;
}

interface GroupDiscussion {
  id: string;
  name: string;
  description: string;
  participant_ids: string[];
  message_count: number;
  last_activity_at: string | null;
}

export default function AllHandsPage() {
  const [messageInput, setMessageInput] = useState("");
  const queryClient = useQueryClient();

  // Fetch All Hands discussion
  const { data: discussion, isLoading: discussionLoading } = useQuery<GroupDiscussion>({
    queryKey: ["group-discussions", "all-hands"],
    queryFn: async () => {
      const response = await fetch(`${API_BASE}/api/v1/group-discussions/all-hands`);
      if (!response.ok) throw new Error("Failed to fetch All Hands discussion");
      return response.json();
    },
  });

  // Fetch active staff members (for display purposes)
  const { data: staffMembers = [] } = useQuery<StaffMember[]>({
    queryKey: ["staff"],
    queryFn: async () => {
      const response = await fetch(`${API_BASE}/api/v1/staff/?is_active=true`);
      if (!response.ok) throw new Error("Failed to fetch staff");
      return response.json();
    },
  });

  // Fetch messages
  const { data: messagesData, isLoading: messagesLoading } = useQuery<{
    messages: Message[];
    total: number;
  }>({
    queryKey: ["group-discussion-messages", discussion?.id],
    queryFn: async () => {
      if (!discussion?.id) return { messages: [], total: 0 };
      const response = await fetch(`${API_BASE}/api/v1/group-discussions/${discussion.id}/messages?limit=100`);
      if (!response.ok) throw new Error("Failed to fetch messages");
      return response.json();
    },
    enabled: !!discussion?.id,
    refetchInterval: 3000, // Poll every 3 seconds for new messages
  });

  // Send message mutation (user message to all staff)
  const sendMessageMutation = useMutation({
    mutationFn: async (content: string) => {
      if (!discussion?.id) throw new Error("No discussion found");

      const response = await fetch(`${API_BASE}/api/v1/group-discussions/${discussion.id}/messages`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          content,
          is_user_message: true,  // This is a message from the user, not a staff member
          staff_id: null,  // No staff_id for user messages
        }),
      });

      if (!response.ok) throw new Error("Failed to send message");
      return response.json();
    },
    onSuccess: () => {
      setMessageInput("");
      queryClient.invalidateQueries({ queryKey: ["group-discussion-messages", discussion?.id] });
      toast.success("Message sent - Staff will respond shortly");
    },
    onError: (error: Error) => {
      toast.error(`Failed to send message: ${error.message}`);
    },
  });

  const handleSendMessage = () => {
    if (!messageInput.trim()) return;
    sendMessageMutation.mutate(messageInput);
  };

  const getStaffInfo = (staffId: string) => {
    return staffMembers.find(s => s.id === staffId);
  };

  return (
    <PageLayout
      title="All Hands"
      isLoading={discussionLoading}
    >
      <div className="flex flex-col h-[calc(100vh-200px)]">
        {/* Header */}
        <Card className="mb-4">
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle className="flex items-center gap-2">
                  <Users className="h-5 w-5" />
                  {discussion?.name || "All Hands"}
                </CardTitle>
                <CardDescription>
                  {discussion?.description || "Company-wide staff discussion"}
                </CardDescription>
              </div>
              <Badge variant="secondary">
                {staffMembers.length} Staff • {messagesData?.total || 0} Messages
              </Badge>
            </div>
          </CardHeader>
        </Card>

        {/* Messages Area */}
        <Card className="flex-1 flex flex-col overflow-hidden">
          <CardContent className="flex-1 overflow-y-auto p-6 space-y-4">
            {messagesLoading ? (
              <div className="text-center text-muted-foreground py-8">Loading messages...</div>
            ) : messagesData && messagesData.messages.length > 0 ? (
              messagesData.messages.map((message) => {
                const staff = message.staff_id ? getStaffInfo(message.staff_id) : null;
                const isUserMessage = message.message_type === "user" && !message.staff_id;
                const isStaffMessage = message.message_type === "assistant" || message.staff_id;

                return (
                  <div key={message.id} className={`flex gap-3 ${isUserMessage ? "flex-row-reverse" : ""}`}>
                    <Avatar className="h-8 w-8 flex-shrink-0">
                      <AvatarFallback className={isUserMessage ? "bg-primary text-primary-foreground" : "bg-secondary"}>
                        {isUserMessage ? "You".substring(0, 2).toUpperCase() : staff?.name.substring(0, 2).toUpperCase() || "??"}
                      </AvatarFallback>
                    </Avatar>
                    <div className={`flex-1 space-y-1 ${isUserMessage ? "items-end" : ""}`}>
                      <div className={`flex items-center gap-2 ${isUserMessage ? "flex-row-reverse" : ""}`}>
                        <span className="font-semibold text-sm">
                          {isUserMessage ? "You" : staff?.name || "Unknown Staff"}
                        </span>
                        {!isUserMessage && staff && (
                          <span className="text-xs text-muted-foreground">
                            @{staff.handle}
                          </span>
                        )}
                        <span className="text-xs text-muted-foreground">
                          {formatDistanceToNow(new Date(message.created_at), { addSuffix: true })}
                        </span>
                      </div>
                      <p className={`text-sm whitespace-pre-wrap ${isUserMessage ? "bg-primary/10 rounded-lg px-3 py-2" : ""}`}>
                        {message.content}
                      </p>
                    </div>
                  </div>
                );
              })
            ) : (
              <div className="text-center text-muted-foreground py-12">
                <Users className="h-12 w-12 mx-auto mb-4 opacity-50" />
                <p>No messages yet. Start the discussion!</p>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Input Area */}
        <Card className="mt-4">
          <CardContent className="p-4">
            <div className="flex gap-2">
              <Textarea
                placeholder="Message all staff members... (Press Enter to send, Shift+Enter for new line)"
                value={messageInput}
                onChange={(e) => setMessageInput(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter" && !e.shiftKey) {
                    e.preventDefault();
                    handleSendMessage();
                  }
                }}
                className="flex-1"
                rows={3}
              />
              <Button
                onClick={handleSendMessage}
                disabled={!messageInput.trim() || sendMessageMutation.isPending}
              >
                <Send className="h-4 w-4" />
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    </PageLayout>
  );
}
