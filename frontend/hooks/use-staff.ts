import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import type { Staff, StaffMessage, StaffConversationHistory } from "@/lib/api/staff";
import * as staffApi from "@/lib/api/staff";

// Fetch all staff
export function useStaff(params?: {
  role_type?: "leadership" | "domain_expert";
  is_active?: boolean;
  limit?: number;
  offset?: number;
}) {
  return useQuery({
    queryKey: ["staff", params],
    queryFn: () => staffApi.fetchStaff(params),
  });
}

// Fetch a single staff member
export function useStaffMember(staffId: string) {
  return useQuery({
    queryKey: ["staff", staffId],
    queryFn: () => staffApi.fetchStaffMember(staffId),
    enabled: !!staffId,
  });
}

// Fetch staff profile with analytics
export function useStaffProfile(staffId: string) {
  return useQuery({
    queryKey: ["staff", staffId, "profile"],
    queryFn: () => staffApi.fetchStaffProfile(staffId),
    enabled: !!staffId,
  });
}

// Fetch staff by handle
export function useStaffByHandle(handle: string) {
  return useQuery({
    queryKey: ["staff", "handle", handle],
    queryFn: () => staffApi.fetchStaffByHandle(handle),
    enabled: !!handle,
  });
}

// Fetch staff conversation
export function useStaffConversation(
  staffId: string,
  params?: {
    limit?: number;
    offset?: number;
  }
) {
  return useQuery({
    queryKey: ["staff", staffId, "conversation", params],
    queryFn: () => staffApi.fetchStaffConversation(staffId, params),
    enabled: !!staffId,
    refetchInterval: 3000, // Refetch every 3s to get new messages
  });
}

// Send a message to staff
export function useSendStaffMessage() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      staffId,
      content,
    }: {
      staffId: string;
      content: string;
    }) => staffApi.sendStaffMessage(staffId, content),
    onSuccess: (_, variables) => {
      // Invalidate conversation to refetch
      queryClient.invalidateQueries({
        queryKey: ["staff", variables.staffId, "conversation"],
      });
    },
  });
}

// Clear staff conversation
export function useClearStaffConversation() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (staffId: string) => staffApi.clearStaffConversation(staffId),
    onSuccess: (_, staffId) => {
      // Invalidate conversation to refetch
      queryClient.invalidateQueries({
        queryKey: ["staff", staffId, "conversation"],
      });
    },
  });
}

// Create staff
export function useCreateStaff() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: Partial<Staff>) => staffApi.createStaff(data),
    onSuccess: () => {
      // Invalidate staff list to refetch
      queryClient.invalidateQueries({
        queryKey: ["staff"],
      });
    },
  });
}

// Update staff
export function useUpdateStaff() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      staffId,
      data,
    }: {
      staffId: string;
      data: Partial<Staff>;
    }) => staffApi.updateStaff(staffId, data),
    onSuccess: (_, variables) => {
      // Invalidate staff queries to refetch
      queryClient.invalidateQueries({
        queryKey: ["staff", variables.staffId],
      });
      queryClient.invalidateQueries({
        queryKey: ["staff"],
      });
    },
  });
}

// Delete staff
export function useDeleteStaff() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (staffId: string) => staffApi.deleteStaff(staffId),
    onSuccess: () => {
      // Invalidate staff list to refetch
      queryClient.invalidateQueries({
        queryKey: ["staff"],
      });
    },
  });
}
