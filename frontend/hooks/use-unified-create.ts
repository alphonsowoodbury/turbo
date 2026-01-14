import { create } from 'zustand';
import { useEffect } from 'react';

export type EntityType = 'note' | 'issue' | 'initiative' | 'milestone' | 'document' | 'project';

export interface ContextData {
  project_id?: string;
  initiative_id?: string;
  milestone_id?: string;
  workspace?: string;
  work_company?: string;
}

interface UnifiedCreateStore {
  isOpen: boolean;
  entityType: EntityType;
  contextData: ContextData | null;

  // Actions
  open: (type?: EntityType, context?: ContextData) => void;
  close: () => void;
  setEntityType: (type: EntityType) => void;
  setContextData: (context: ContextData) => void;
}

export const useUnifiedCreate = create<UnifiedCreateStore>((set) => ({
  isOpen: false,
  entityType: 'note',
  contextData: null,

  open: (type = 'note', context = null) =>
    set({ isOpen: true, entityType: type, contextData: context }),

  close: () =>
    set({ isOpen: false, contextData: null }),

  setEntityType: (type) =>
    set({ entityType: type }),

  setContextData: (context) =>
    set({ contextData: context }),
}));

// Global keyboard shortcut hook
export function useUnifiedCreateShortcut() {
  const open = useUnifiedCreate((state) => state.open);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Cmd+K or Ctrl+K
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault();
        open();
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [open]);
}
