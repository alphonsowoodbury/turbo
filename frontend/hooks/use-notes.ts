import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { notesApi } from "@/lib/api/notes";
import type { Note, NoteCreate, NoteUpdate } from "@/lib/types";

export function useNotes(params?: {
  workspace?: string;
  work_company?: string;
  include_archived?: boolean;
  limit?: number;
  offset?: number;
}) {
  return useQuery({
    queryKey: ["notes", params],
    queryFn: () => notesApi.list(params),
  });
}

export function useNote(id: string | null) {
  return useQuery({
    queryKey: ["notes", id],
    queryFn: () => notesApi.get(id!),
    enabled: !!id,
  });
}

export function useSearchNotes(params: {
  q: string;
  workspace?: string;
  include_archived?: boolean;
}) {
  return useQuery({
    queryKey: ["notes", "search", params],
    queryFn: () => notesApi.search(params),
    enabled: params.q.length > 0,
  });
}

export function useCreateNote() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: NoteCreate) => notesApi.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["notes"] });
    },
  });
}

export function useUpdateNote() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: NoteUpdate }) =>
      notesApi.update(id, data),
    onSuccess: (note) => {
      queryClient.invalidateQueries({ queryKey: ["notes"] });
      queryClient.invalidateQueries({ queryKey: ["notes", note.id] });
    },
  });
}

export function useDeleteNote() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) => notesApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["notes"] });
    },
  });
}
