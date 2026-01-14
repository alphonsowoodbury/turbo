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
import { useCreateDocument } from '@/hooks/use-documents';
import { useProjects } from '@/hooks/use-projects';
import type { ContextData } from '@/hooks/use-unified-create';

interface DocumentFormData {
  title: string;
  content: string;
  type: string;
  format: string;
  status: string;
  project_id: string;
}

interface DocumentFormProps {
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

export function DocumentForm({ contextData, onSuccess }: DocumentFormProps) {
  const { data: projects } = useProjects();

  const form = useForm<DocumentFormData>({
    defaultValues: {
      title: '',
      content: '',
      type: 'specification',
      format: 'markdown',
      status: 'draft',
      project_id: contextData?.project_id || '',
    }
  });

  const createDocument = useCreateDocument();

  const onSubmit = form.handleSubmit(async (data) => {
    try {
      // Validate project selection
      if (!data.project_id) {
        toast.error('Please select a project');
        return;
      }

      await createDocument.mutateAsync(data);
      toast.success('Document created successfully!');
      form.reset();
      onSuccess();
    } catch (error) {
      toast.error(
        error instanceof Error
          ? error.message
          : 'Failed to create document'
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
          placeholder="Document title"
          {...form.register('title', { required: true })}
        />
      </motion.div>

      {/* Content */}
      <motion.div
        variants={fieldVariants}
        custom={1}
        initial="hidden"
        animate="visible"
      >
        <Label htmlFor="content">
          Content <span className="text-destructive">*</span>
        </Label>
        <Textarea
          id="content"
          rows={6}
          placeholder="Document content (supports markdown)..."
          {...form.register('content', { required: true })}
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
          render={({ field }) => (
            <Select
              value={field.value || ''}
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

      {/* Type, Format, Status */}
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
                  <SelectItem value="specification">Specification</SelectItem>
                  <SelectItem value="user_guide">User Guide</SelectItem>
                  <SelectItem value="api_doc">API Doc</SelectItem>
                  <SelectItem value="readme">README</SelectItem>
                  <SelectItem value="changelog">Changelog</SelectItem>
                  <SelectItem value="requirements">Requirements</SelectItem>
                  <SelectItem value="design">Design</SelectItem>
                  <SelectItem value="adr">ADR</SelectItem>
                  <SelectItem value="other">Other</SelectItem>
                </SelectContent>
              </Select>
            )}
          />
        </div>

        {/* Format */}
        <div className="grid gap-2">
          <Label htmlFor="format">Format</Label>
          <Controller
            name="format"
            control={form.control}
            render={({ field }) => (
              <Select value={field.value} onValueChange={field.onChange}>
                <SelectTrigger id="format">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="markdown">Markdown</SelectItem>
                  <SelectItem value="html">HTML</SelectItem>
                  <SelectItem value="text">Text</SelectItem>
                  <SelectItem value="pdf">PDF</SelectItem>
                  <SelectItem value="docx">DOCX</SelectItem>
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
                  <SelectItem value="draft">Draft</SelectItem>
                  <SelectItem value="in_review">In Review</SelectItem>
                  <SelectItem value="approved">Approved</SelectItem>
                  <SelectItem value="published">Published</SelectItem>
                  <SelectItem value="archived">Archived</SelectItem>
                </SelectContent>
              </Select>
            )}
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
          disabled={createDocument.isPending}
        >
          {createDocument.isPending ? 'Creating...' : 'Create Document'}
        </Button>
      </motion.div>
    </form>
  );
}
