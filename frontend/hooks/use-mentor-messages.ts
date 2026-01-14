import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  fetchConversation,
  sendMessage,
  updateMessage,
  clearConversation,
  ConversationHistory,
  SendMessageResponse,
  MentorMessage,
} from "@/lib/api/mentors";

// Fetch conversation history for a mentor
export function useMentorMessages(
  mentorId: string | undefined,
  params?: {
    limit?: number;
    offset?: number;
  }
) {
  return useQuery<ConversationHistory>({
    queryKey: ["mentor-messages", mentorId, params],
    queryFn: () => fetchConversation(mentorId!, params),
    enabled: !!mentorId,
  });
}

// Send a message to a mentor
export function useSendMessage() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ mentorId, content }: { mentorId: string; content: string }) =>
      sendMessage(mentorId, content),
    onSuccess: (data: SendMessageResponse, variables) => {
      // Invalidate conversation history to refresh messages
      queryClient.invalidateQueries({
        queryKey: ["mentor-messages", variables.mentorId],
      });
      // Also invalidate mentor to update message count
      queryClient.invalidateQueries({
        queryKey: ["mentors", variables.mentorId],
      });
    },
  });
}

// Update a message
export function useUpdateMessage() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ mentorId, messageId, content }: { mentorId: string; messageId: string; content: string }) =>
      updateMessage(mentorId, messageId, content),
    onSuccess: (data: MentorMessage, variables) => {
      // Invalidate conversation history to refresh messages
      queryClient.invalidateQueries({
        queryKey: ["mentor-messages", variables.mentorId],
      });
    },
  });
}

// Clear conversation history
export function useClearConversation() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (mentorId: string) => clearConversation(mentorId),
    onSuccess: (data, mentorId) => {
      // Invalidate conversation history
      queryClient.invalidateQueries({
        queryKey: ["mentor-messages", mentorId],
      });
      // Also invalidate mentor to update message count
      queryClient.invalidateQueries({
        queryKey: ["mentors", mentorId],
      });
    },
  });
}
