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
import { useCreateIssue } from '@/hooks/use-issues';
import { useProjects } from '@/hooks/use-projects';
import type { ContextData } from '@/hooks/use-unified-create';
import type { IssueCreate, IssueType, IssueStatus, Priority } from '@/lib/types';

interface IssueFormProps {
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

export function IssueForm({ contextData, onSuccess }: IssueFormProps) {
  const { data: projects } = useProjects();

  const form = useForm<IssueCreate>({
    defaultValues: {
      title: '',
      description: '',
      type: 'task',
      status: 'open',
      priority: 'medium',
      project_id: contextData?.project_id,
      assignee: undefined,
    }
  });

  const createIssue = useCreateIssue();
  const watchType = form.watch('type');

  const onSubmit = form.handleSubmit(async (data) => {
    try {
      // Validate: discovery issues don't need a project, others do
      if (data.type !== 'discovery' && !data.project_id) {
        toast.error('Please select a project');
        return;
      }

      await createIssue.mutateAsync(data);
      toast.success('Issue created successfully!');
      form.reset();
      onSuccess();
    } catch (error) {
      toast.error(
        error instanceof Error
          ? error.message
          : 'Failed to create issue'
      );
    }
  });

  return (
    <form onSubmit={onSubmit} className="space-y-4 p-4">
      {/* Title */}
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
          placeholder="Issue title"
          {...form.register('title', { required: true })}
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
          placeholder="Describe the issue..."
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
          Project {watchType !== 'discovery' && <span className="text-destructive">*</span>}
        </Label>
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
                <SelectValue
                  placeholder={
                    watchType === 'discovery'
                      ? 'Select a project (optional)'
                      : 'Select a project'
                  }
                />
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
        {watchType === 'discovery' && (
          <p className="text-xs text-muted-foreground mt-1">
            Discovery issues can exist independently of projects
          </p>
        )}
      </motion.div>

      {/* Type, Status, Priority - 3 columns */}
      <motion.div
        variants={fieldVariants}
        custom={3}
        initial="hidden"
        animate="visible"
        className="grid grid-cols-3 gap-4"
      >
        {/* Type */}
        <div className="grid gap-2">
          <Label htmlFor="type">Type</Label>
          <Controller
            name="type"
            control={form.control}
            render={({ field }) => (
              <Select value={field.value} onValueChange={field.onChange}>
                <SelectTrigger id="type">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="feature">Feature</SelectItem>
                  <SelectItem value="bug">Bug</SelectItem>
                  <SelectItem value="task">Task</SelectItem>
                  <SelectItem value="enhancement">Enhancement</SelectItem>
                  <SelectItem value="documentation">Documentation</SelectItem>
                  <SelectItem value="discovery">Discovery</SelectItem>
                </SelectContent>
              </Select>
            )}
          />
        </div>

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
                  <SelectItem value="open">Open</SelectItem>
                  <SelectItem value="ready">Ready</SelectItem>
                  <SelectItem value="in_progress">In Progress</SelectItem>
                  <SelectItem value="review">Review</SelectItem>
                  <SelectItem value="testing">Testing</SelectItem>
                  <SelectItem value="closed">Closed</SelectItem>
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
      </motion.div>

      {/* Assignee */}
      <motion.div
        variants={fieldVariants}
        custom={4}
        initial="hidden"
        animate="visible"
      >
        <Label htmlFor="assignee">Assignee (email)</Label>
        <Input
          id="assignee"
          type="email"
          placeholder="user@example.com"
          {...form.register('assignee')}
        />
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
          disabled={createIssue.isPending}
        >
          {createIssue.isPending ? 'Creating...' : 'Create Issue'}
        </Button>
      </motion.div>
    </form>
  );
}
