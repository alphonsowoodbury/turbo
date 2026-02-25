"use client";

import { useForm, Controller } from 'react-hook-form';
import { motion } from 'framer-motion';
import { toast } from 'sonner';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Button } from '@/components/ui/button';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { useCreateInitiative } from '@/hooks/use-initiatives';
import { useProjects } from '@/hooks/use-projects';
import type { ContextData } from '@/hooks/use-unified-create';
import type { InitiativeCreate, InitiativeStatus } from '@/lib/types';

interface InitiativeFormProps {
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

export function InitiativeForm({ contextData, onSuccess }: InitiativeFormProps) {
  const { data: projects } = useProjects();

  const form = useForm<InitiativeCreate>({
    defaultValues: {
      name: '',
      description: '',
      status: 'planning',
      project_id: contextData?.project_id,
      start_date: undefined,
      target_date: undefined,
    }
  });

  const createInitiative = useCreateInitiative();

  const onSubmit = form.handleSubmit(async (data) => {
    try {
      await createInitiative.mutateAsync(data);
      toast.success('Initiative created successfully!');
      form.reset();
      onSuccess();
    } catch (error) {
      toast.error(
        error instanceof Error
          ? error.message
          : 'Failed to create initiative'
      );
    }
  });

  return (
    <form onSubmit={onSubmit} className="space-y-4 p-4">
      {/* Name */}
      <motion.div
        variants={fieldVariants}
        custom={0}
        initial="hidden"
        animate="visible"
      >
        <Label htmlFor="name">
          Name <span className="text-destructive">*</span>
        </Label>
        <Input
          id="name"
          autoFocus
          placeholder="Initiative name"
          {...form.register('name', { required: true })}
        />
      </motion.div>

      {/* Description */}
      <motion.div
        variants={fieldVariants}
        custom={1}
        initial="hidden"
        animate="visible"
      >
        <Label htmlFor="description">
          Description <span className="text-destructive">*</span>
        </Label>
        <Textarea
          id="description"
          rows={4}
          placeholder="Describe the initiative goals and scope..."
          {...form.register('description', { required: true })}
        />
      </motion.div>

      {/* Project (Optional) */}
      <motion.div
        variants={fieldVariants}
        custom={2}
        initial="hidden"
        animate="visible"
      >
        <Label htmlFor="project">Project (Optional)</Label>
        <Controller
          name="project_id"
          control={form.control}
          render={({ field }) => (
            <Select
              value={field.value || ''}
              onValueChange={(value) => field.onChange(value || undefined)}
              disabled={!!contextData?.project_id}
            >
              <SelectTrigger id="project">
                <SelectValue placeholder="Select a project (optional)" />
              </SelectTrigger>
              <SelectContent>
                {projects?.map((project) => (
                  <SelectItem key={project.id} value={project.id}>
                    {project.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          )}
        />
        <p className="text-xs text-muted-foreground mt-1">
          Initiatives can span multiple projects or exist independently
        </p>
      </motion.div>

      {/* Status and Dates */}
      <motion.div
        variants={fieldVariants}
        custom={3}
        initial="hidden"
        animate="visible"
        className="grid grid-cols-3 gap-4"
      >
        {/* Status */}
        <div className="grid gap-2">
          <Label htmlFor="status">Status</Label>
          <Controller
            name="status"
            control={form.control}
            render={({ field }) => (
              <Select value={field.value} onValueChange={field.onChange}>
                <SelectTrigger id="status">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="planning">Planning</SelectItem>
                  <SelectItem value="in_progress">In Progress</SelectItem>
                  <SelectItem value="on_hold">On Hold</SelectItem>
                  <SelectItem value="completed">Completed</SelectItem>
                  <SelectItem value="cancelled">Cancelled</SelectItem>
                </SelectContent>
              </Select>
            )}
          />
        </div>

        {/* Start Date */}
        <div className="grid gap-2">
          <Label htmlFor="start_date">Start Date</Label>
          <Input
            id="start_date"
            type="date"
            {...form.register('start_date')}
          />
        </div>

        {/* Target Date */}
        <div className="grid gap-2">
          <Label htmlFor="target_date">Target Date</Label>
          <Input
            id="target_date"
            type="date"
            {...form.register('target_date')}
          />
        </div>
      </motion.div>

      {/* Submit Button */}
      <motion.div
        variants={fieldVariants}
        custom={4}
        initial="hidden"
        animate="visible"
        className="flex justify-end gap-2 pt-2"
      >
        <Button
          type="submit"
          disabled={createInitiative.isPending}
        >
          {createInitiative.isPending ? 'Creating...' : 'Create Initiative'}
        </Button>
      </motion.div>
    </form>
  );
}
