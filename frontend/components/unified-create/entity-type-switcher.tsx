"use client";

import { motion } from 'framer-motion';
import {
  StickyNote,
  Bug,
  Target,
  Flag,
  FileText,
  Folder,
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { useUnifiedCreate, type EntityType } from '@/hooks/use-unified-create';

const entityTypes = [
  { type: 'note' as const, label: 'Note', icon: StickyNote },
  { type: 'issue' as const, label: 'Issue', icon: Bug },
  { type: 'initiative' as const, label: 'Initiative', icon: Target },
  { type: 'milestone' as const, label: 'Milestone', icon: Flag },
  { type: 'document' as const, label: 'Document', icon: FileText },
  { type: 'project' as const, label: 'Project', icon: Folder },
];

export function EntityTypeSwitcher() {
  const { entityType, setEntityType } = useUnifiedCreate();

  return (
    <div className="flex gap-2 p-2 border-b overflow-x-auto">
      {entityTypes.map(({ type, label, icon: Icon }) => (
        <button
          key={type}
          onClick={() => setEntityType(type)}
          className={cn(
            "relative px-3 py-1.5 text-sm rounded-md transition-colors flex-shrink-0",
            "flex items-center gap-2",
            entityType === type
              ? "text-foreground"
              : "text-muted-foreground hover:text-foreground"
          )}
        >
          {entityType === type && (
            <motion.div
              layoutId="active-entity-bg"
              className="absolute inset-0 bg-muted rounded-md"
              transition={{ type: "spring", bounce: 0.2, duration: 0.5 }}
            />
          )}
          <Icon className="w-4 h-4 relative z-10" />
          <span className="relative z-10">{label}</span>
        </button>
      ))}
    </div>
  );
}
