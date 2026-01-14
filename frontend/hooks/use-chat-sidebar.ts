import { create } from "zustand";
import { persist } from "zustand/middleware";

interface ChatSidebarState {
  // Panel state
  isOpen: boolean;
  width: number; // 300-600px

  // Active mentor
  activeMentorId: string | null;

  // Actions
  toggle: () => void;
  open: (mentorId?: string) => void;
  close: () => void;
  setWidth: (width: number) => void;
  setActiveMentor: (mentorId: string | null) => void;
}

const DEFAULT_WIDTH = 400;
const MIN_WIDTH = 300;
const MAX_WIDTH = 600;

export const useChatSidebar = create<ChatSidebarState>()(
  persist(
    (set, get) => ({
      // Initial state
      isOpen: false,
      width: DEFAULT_WIDTH,
      activeMentorId: null,

      // Toggle panel open/closed
      toggle: () => {
        set((state) => ({ isOpen: !state.isOpen }));
      },

      // Open panel with optional mentor
      open: (mentorId?: string) => {
        set({
          isOpen: true,
          ...(mentorId && { activeMentorId: mentorId }),
        });
      },

      // Close panel
      close: () => {
        set({ isOpen: false });
      },

      // Set panel width with constraints
      setWidth: (width: number) => {
        const constrainedWidth = Math.max(MIN_WIDTH, Math.min(width, MAX_WIDTH));
        set({ width: constrainedWidth });
      },

      // Set active mentor
      setActiveMentor: (mentorId: string | null) => {
        set({ activeMentorId: mentorId });
        // Auto-open if mentor is selected
        if (mentorId && !get().isOpen) {
          set({ isOpen: true });
        }
      },
    }),
    {
      name: "chat-sidebar-storage",
      // Persist these fields
      partialize: (state) => ({
        isOpen: state.isOpen,
        width: state.width,
        activeMentorId: state.activeMentorId,
      }),
    }
  )
);
