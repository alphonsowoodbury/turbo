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
import { useCreateMilestone } from '@/hooks/use-milestones';
import { useProjects } from '@/hooks/use-projects';
import type { ContextData } from '@/hooks/use-unified-create';
import type { MilestoneCreate, MilestoneStatus } from '@/lib/types';

interface MilestoneFormProps {
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

export function MilestoneForm({ contextData, onSuccess }: MilestoneFormProps) {
  const { data: projects } = useProjects();

  const form = useForm<MilestoneCreate>({
    defaultValues: {
      name: '',
      description: '',
      status: 'planned',
      project_id: contextData?.project_id || '',
      start_date: undefined,
      due_date: '',
    }
  });

  const createMilestone = useCreateMilestone();

  const onSubmit = form.handleSubmit(async (data) => {
    try {
      // Validate required fields
      if (!data.project_id) {
        toast.error('Please select a project');
        return;
      }

      if (!data.due_date) {
        toast.error('Please set a due date');
        return;
      }

      await createMilestone.mutateAsync(data);
      toast.success('Milestone created successfully!');
      form.reset();
      onSuccess();
    } catch (error) {
      toast.error(
        error instanceof Error
          ? error.message
          : 'Failed to create milestone'
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
          placeholder="Milestone name"
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
          rows={3}
          placeholder="Describe the milestone deliverables..."
          {...form.register('description', { required: true })}
        />
      </motion.div>

      {/* Project */}
      <motion.div
        variants={fieldVariants}
        custom={2}
        initial="hidden"
        animate="visible"
      >
        <Label htmlFor="project">
          Project <span className="text-destructive">*</span>
        </Label>
        <Controller
          name="project_id"
          control={form.control}
          rules={{ required: true }}
          render={({ field }) => (
            <Select
              value={field.value}
              onValueChange={field.onChange}
              disabled={!!contextData?.project_id}
            >
              <SelectTrigger id="project">
                <SelectValue placeholder="Select a project" />
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
                  <SelectItem value="planned">Planned</SelectItem>
                  <SelectItem value="in_progress">In Progress</SelectItem>
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

        {/* Due Date */}
        <div className="grid gap-2">
          <Label htmlFor="due_date">
            Due Date <span className="text-destructive">*</span>
          </Label>
          <Input
            id="due_date"
            type="date"
            {...form.register('due_date', { required: true })}
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
          disabled={createMilestone.isPending}
        >
          {createMilestone.isPending ? 'Creating...' : 'Create Milestone'}
        </Button>
      </motion.div>
    </form>
  );
}
