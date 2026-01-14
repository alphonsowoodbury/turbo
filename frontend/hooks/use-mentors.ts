import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  fetchMentors,
  fetchMentor,
  createMentor,
  updateMentor,
  deleteMentor,
  CreateMentorData,
  UpdateMentorData,
  Mentor,
} from "@/lib/api/mentors";

// Fetch all mentors with optional filters
export function useMentors(params?: {
  workspace?: string;
  work_company?: string;
  is_active?: boolean;
  limit?: number;
  offset?: number;
}) {
  return useQuery<Mentor[]>({
    queryKey: ["mentors", params],
    queryFn: () => fetchMentors(params),
  });
}

// Fetch a specific mentor
export function useMentor(mentorId: string | undefined) {
  return useQuery<Mentor>({
    queryKey: ["mentors", mentorId],
    queryFn: () => fetchMentor(mentorId!),
    enabled: !!mentorId,
  });
}

// Create a new mentor
export function useCreateMentor() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: CreateMentorData) => createMentor(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["mentors"] });
    },
  });
}

// Update a mentor
export function useUpdateMentor() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ mentorId, data }: { mentorId: string; data: UpdateMentorData }) =>
      updateMentor(mentorId, data),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ["mentors", data.id] });
      queryClient.invalidateQueries({ queryKey: ["mentors"] });
    },
  });
}

// Delete a mentor
export function useDeleteMentor() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (mentorId: string) => deleteMentor(mentorId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["mentors"] });
    },
  });
}
