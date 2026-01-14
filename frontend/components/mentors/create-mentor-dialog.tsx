"use client";

import { useState } from "react";
import { useCreateMentor } from "@/hooks/use-mentors";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { toast } from "sonner";

interface CreateMentorDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function CreateMentorDialog({ open, onOpenChange }: CreateMentorDialogProps) {
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [persona, setPersona] = useState("");
  const [workspace, setWorkspace] = useState<"personal" | "freelance" | "work">("personal");
  const [workCompany, setWorkCompany] = useState("");

  const createMentorMutation = useCreateMentor();

  const handleCreate = async () => {
    // Validation
    if (!name.trim()) {
      toast.error("Validation Error", {
        description: "Mentor name is required.",
      });
      return;
    }

    if (!description.trim()) {
      toast.error("Validation Error", {
        description: "Description is required.",
      });
      return;
    }

    if (!persona.trim()) {
      toast.error("Validation Error", {
        description: "Persona is required.",
      });
      return;
    }

    try {
      await createMentorMutation.mutateAsync({
        name: name.trim(),
        description: description.trim(),
        persona: persona.trim(),
        workspace,
        work_company: workspace === "work" && workCompany.trim() ? workCompany.trim() : undefined,
        is_active: true,
      });

      // Reset form
      setName("");
      setDescription("");
      setPersona("");
      setWorkspace("personal");
      setWorkCompany("");

      onOpenChange(false);
      toast.success("Mentor Created", {
        description: "Your new mentor has been created successfully.",
      });
    } catch (error) {
      toast.error("Error", {
        description: "Failed to create mentor. Please try again.",
      });
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-3xl max-h-[80vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>Create New Mentor</DialogTitle>
          <DialogDescription>
            Create a new AI mentor with a custom persona to guide and support your work in specific areas.
          </DialogDescription>
        </DialogHeader>
        <div className="space-y-4 py-4">
          <div className="space-y-2">
            <Label htmlFor="name">Name *</Label>
            <Input
              id="name"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="e.g., Senior Engineer Mentor, Product Strategy Advisor"
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="workspace">Workspace *</Label>
            <Select
              value={workspace}
              onValueChange={(value: "personal" | "freelance" | "work") => setWorkspace(value)}
            >
              <SelectTrigger id="workspace">
                <SelectValue placeholder="Select workspace" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="personal">Personal</SelectItem>
                <SelectItem value="freelance">Freelance</SelectItem>
                <SelectItem value="work">Work</SelectItem>
              </SelectContent>
            </Select>
            <p className="text-xs text-muted-foreground">
              Choose which workspace this mentor belongs to
            </p>
          </div>

          {workspace === "work" && (
            <div className="space-y-2">
              <Label htmlFor="work_company">Company Name</Label>
              <Input
                id="work_company"
                value={workCompany}
                onChange={(e) => setWorkCompany(e.target.value)}
                placeholder="e.g., Acme Corp"
              />
              <p className="text-xs text-muted-foreground">
                Optional: Specify the company name for work workspace
              </p>
            </div>
          )}

          <div className="space-y-2">
            <Label htmlFor="description">Description *</Label>
            <Textarea
              id="description"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Brief description of this mentor's purpose and expertise"
              rows={3}
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="persona">Persona *</Label>
            <Textarea
              id="persona"
              value={persona}
              onChange={(e) => setPersona(e.target.value)}
              placeholder="Define how this mentor communicates, their approach to mentorship, expertise areas, and communication style. Be specific about what makes them unique."
              rows={15}
              className="font-mono text-sm"
            />
            <p className="text-xs text-muted-foreground">
              The persona defines how your mentor will communicate and approach conversations. Be specific about their
              style, expertise, communication patterns, and how they provide guidance. This is the core of your mentor's
              personality.
            </p>
          </div>
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            Cancel
          </Button>
          <Button onClick={handleCreate} disabled={createMentorMutation.isPending}>
            {createMentorMutation.isPending ? "Creating..." : "Create Mentor"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
