"use client";

import { useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from '@/components/ui/dialog';
import { useUnifiedCreate } from '@/hooks/use-unified-create';
import { EntityTypeSwitcher } from './entity-type-switcher';
import { NoteForm } from './forms/note-form';
import { IssueForm } from './forms/issue-form';
import { InitiativeForm } from './forms/initiative-form';
import { MilestoneForm } from './forms/milestone-form';
import { DocumentForm } from './forms/document-form';
import { ProjectForm } from './forms/project-form';

const containerVariants = {
  hidden: { opacity: 0, scale: 0.95 },
  visible: {
    opacity: 1,
    scale: 1,
    transition: {
      duration: 0.2,
      ease: [0.16, 1, 0.3, 1] as const
    }
  },
  exit: {
    opacity: 0,
    scale: 0.95,
    transition: { duration: 0.15 }
  }
};

export function UnifiedCreateModal() {
  const { isOpen, close, entityType, contextData } = useUnifiedCreate();

  // Handle Escape key
  useEffect(() => {
    if (!isOpen) return;

    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        close();
      }
    };

    window.addEventListener('keydown', handleEscape);
    return () => window.removeEventListener('keydown', handleEscape);
  }, [isOpen, close]);

  const handleSuccess = () => {
    close();
  };

  return (
    <Dialog open={isOpen} onOpenChange={close}>
      <DialogContent className="sm:max-w-[600px] p-0 overflow-hidden">
        <DialogHeader className="px-6 pt-6 pb-0">
          <DialogTitle>Create...</DialogTitle>
          <DialogDescription className="sr-only">
            Create a new entity by selecting a type and filling in the form
          </DialogDescription>
        </DialogHeader>

        <EntityTypeSwitcher />

        <AnimatePresence mode="wait">
          <motion.div
            key={entityType}
            variants={containerVariants}
            initial="hidden"
            animate="visible"
            exit="exit"
          >
            {entityType === 'note' && (
              <NoteForm contextData={contextData} onSuccess={handleSuccess} />
            )}
            {entityType === 'issue' && (
              <IssueForm contextData={contextData} onSuccess={handleSuccess} />
            )}
            {entityType === 'initiative' && (
              <InitiativeForm contextData={contextData} onSuccess={handleSuccess} />
            )}
            {entityType === 'milestone' && (
              <MilestoneForm contextData={contextData} onSuccess={handleSuccess} />
            )}
            {entityType === 'document' && (
              <DocumentForm contextData={contextData} onSuccess={handleSuccess} />
            )}
            {entityType === 'project' && (
              <ProjectForm contextData={contextData} onSuccess={handleSuccess} />
            )}
          </motion.div>
        </AnimatePresence>
      </DialogContent>
    </Dialog>
  );
}
