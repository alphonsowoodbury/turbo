"use client";

import { useForm } from 'react-hook-form';
import { motion } from 'framer-motion';
import { useCreateNote } from '@/hooks/use-notes';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Button } from '@/components/ui/button';
import { toast } from 'sonner';
import type { ContextData } from '@/hooks/use-unified-create';
import type { NoteCreate } from '@/lib/types';

interface NoteFormProps {
  contextData: ContextData | null;
  onSuccess: () => void;
}

const fieldVariants = {
  hidden: { opacity: 0, y: 10 },
  visible: (i: number) => ({
    opacity: 1,
    y: 0,
    transition: {
      delay: i * 0.05,
      duration: 0.2,
      ease: [0.16, 1, 0.3, 1] as const
    }
  }),
};

export function NoteForm({ contextData, onSuccess }: NoteFormProps) {
  const form = useForm<NoteCreate>({
    defaultValues: {
      title: '',
      content: '',
      workspace: (contextData?.workspace as any) ?? 'personal',
      work_company: contextData?.work_company,
    }
  });

  const createNote = useCreateNote();

  const onSubmit = form.handleSubmit(async (data) => {
    try {
      await createNote.mutateAsync(data);
      toast.success('Note created successfully!');
      form.reset();
      onSuccess();
    } catch (error) {
      toast.error(error instanceof Error ? error.message : 'Failed to create note');
    }
  });

  return (
    <form onSubmit={onSubmit} className="space-y-4 p-4">
      <motion.div
        variants={fieldVariants}
        custom={0}
        initial="hidden"
        animate="visible"
      >
        <Label htmlFor="title">
          Title <span className="text-destructive">*</span>
        </Label>
        <Input
          id="title"
          autoFocus
          placeholder="Quick note about..."
          {...form.register('title', { required: true })}
        />
      </motion.div>

      <motion.div
        variants={fieldVariants}
        custom={1}
        initial="hidden"
        animate="visible"
      >
        <Label htmlFor="content">Content</Label>
        <Textarea
          id="content"
          rows={4}
          placeholder="Add more details..."
          {...form.register('content')}
        />
      </motion.div>

      <motion.div
        variants={fieldVariants}
        custom={2}
        initial="hidden"
        animate="visible"
        className="flex justify-end gap-2 pt-2"
      >
        <Button
          type="submit"
          disabled={createNote.isPending}
        >
          {createNote.isPending ? 'Creating...' : 'Create Note'}
        </Button>
      </motion.div>
    </form>
  );
}
