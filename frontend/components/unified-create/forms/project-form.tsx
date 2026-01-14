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
import { useCreateProject } from '@/hooks/use-projects';
import type { ContextData } from '@/hooks/use-unified-create';
import type { ProjectCreate, ProjectStatus, Priority } from '@/lib/types';

interface ProjectFormProps {
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
      ease: [0.16, 1, 0.3, 1]
    }
  }),
};

export function ProjectForm({ contextData, onSuccess }: ProjectFormProps) {
  const form = useForm<ProjectCreate>({
    defaultValues: {
      name: '',
      project_key: '',
      description: '',
      priority: 'medium',
      status: 'active',
      completion_percentage: 0,
      is_archived: false,
      repository_path: '',
    }
  });

  const createProject = useCreateProject();

  const onSubmit = form.handleSubmit(async (data) => {
    try {
      await createProject.mutateAsync(data);
      toast.success('Project created successfully!');
      form.reset();
      onSuccess();
    } catch (error) {
      toast.error(
        error instanceof Error
          ? error.message
          : 'Failed to create project'
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
          placeholder="Project name"
          {...form.register('name', { required: true })}
        />
      </motion.div>

      {/* Project Key */}
      <motion.div
        variants={fieldVariants}
        custom={1}
        initial="hidden"
        animate="visible"
      >
        <Label htmlFor="project_key">
          Project Key <span className="text-destructive">*</span>
        </Label>
        <Input
          id="project_key"
          placeholder="PROJ (2-10 uppercase letters/numbers)"
          {...form.register('project_key', {
            required: true,
            pattern: {
              value: /^[A-Z][A-Z0-9]{1,9}$/,
              message: 'Must start with a letter and contain only uppercase letters/numbers'
            }
          })}
        />
        <p className="text-xs text-muted-foreground mt-1">
          Unique identifier for this project (e.g., CNTXT, TURBO)
        </p>
      </motion.div>

      {/* Description */}
      <motion.div
        variants={fieldVariants}
        custom={2}
        initial="hidden"
        animate="visible"
      >
        <Label htmlFor="description">
          Description <span className="text-destructive">*</span>
        </Label>
        <Textarea
          id="description"
          rows={4}
          placeholder="Describe the project goals and scope..."
          {...form.register('description', { required: true })}
        />
      </motion.div>

      {/* Repository Path */}
      <motion.div
        variants={fieldVariants}
        custom={3}
        initial="hidden"
        animate="visible"
      >
        <Label htmlFor="repository_path">
          Repository Path
        </Label>
        <Input
          id="repository_path"
          placeholder="/path/to/git/repository (optional)"
          {...form.register('repository_path')}
        />
        <p className="text-xs text-muted-foreground mt-1">
          Local filesystem path to the git repository for this project
        </p>
      </motion.div>

      {/* Status, Priority, Completion */}
      <motion.div
        variants={fieldVariants}
        custom={4}
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
                  <SelectItem value="active">Active</SelectItem>
                  <SelectItem value="on_hold">On Hold</SelectItem>
                  <SelectItem value="completed">Completed</SelectItem>
                  <SelectItem value="archived">Archived</SelectItem>
                </SelectContent>
              </Select>
            )}
          />
        </div>

        {/* Priority */}
        <div className="grid gap-2">
          <Label htmlFor="priority">Priority</Label>
          <Controller
            name="priority"
            control={form.control}
            render={({ field }) => (
              <Select value={field.value} onValueChange={field.onChange}>
                <SelectTrigger id="priority">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="low">Low</SelectItem>
                  <SelectItem value="medium">Medium</SelectItem>
                  <SelectItem value="high">High</SelectItem>
                  <SelectItem value="critical">Critical</SelectItem>
                </SelectContent>
              </Select>
            )}
          />
        </div>

        {/* Completion Percentage */}
        <div className="grid gap-2">
          <Label htmlFor="completion">Completion %</Label>
          <Input
            id="completion"
            type="number"
            min="0"
            max="100"
            placeholder="0"
            {...form.register('completion_percentage', {
              valueAsNumber: true,
              min: 0,
              max: 100,
            })}
          />
        </div>
      </motion.div>

      {/* Submit Button */}
      <motion.div
        variants={fieldVariants}
        custom={5}
        initial="hidden"
        animate="visible"
        className="flex justify-end gap-2 pt-2"
      >
        <Button
          type="submit"
          disabled={createProject.isPending}
        >
          {createProject.isPending ? 'Creating...' : 'Create Project'}
        </Button>
      </motion.div>
    </form>
  );
}
