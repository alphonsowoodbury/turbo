"use client";

import { useState } from "react";
import { Mentor } from "@/lib/api/mentors";
import { useUpdateMentor } from "@/hooks/use-mentors";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Edit2 } from "lucide-react";
import { toast } from "sonner";

interface EditMentorDialogProps {
  mentor: Mentor;
}

export function EditMentorDialog({ mentor }: EditMentorDialogProps) {
  const [open, setOpen] = useState(false);
  const [name, setName] = useState(mentor.name);
  const [description, setDescription] = useState(mentor.description);
  const [persona, setPersona] = useState(mentor.persona);

  const updateMentorMutation = useUpdateMentor();

  const handleSave = async () => {
    try {
      await updateMentorMutation.mutateAsync({
        mentorId: mentor.id,
        data: {
          name,
          description,
          persona,
        },
      });
      setOpen(false);
      toast.success("Mentor Updated", {
        description: "Your mentor's persona has been updated successfully.",
      });
    } catch (error) {
      toast.error("Error", {
        description: "Failed to update mentor. Please try again.",
      });
    }
  };

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button variant="outline" size="sm">
          <Edit2 className="h-4 w-4 mr-2" />
          Edit Mentor
        </Button>
      </DialogTrigger>
      <DialogContent className="max-w-3xl max-h-[80vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>Edit Mentor</DialogTitle>
          <DialogDescription>
            Update your mentor's name, description, and persona to refine their communication style and approach.
          </DialogDescription>
        </DialogHeader>
        <div className="space-y-4 py-4">
          <div className="space-y-2">
            <Label htmlFor="name">Name</Label>
            <Input
              id="name"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="Mentor name"
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="description">Description</Label>
            <Textarea
              id="description"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Brief description of this mentor"
              rows={3}
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="persona">Persona</Label>
            <Textarea
              id="persona"
              value={persona}
              onChange={(e) => setPersona(e.target.value)}
              placeholder="Define how this mentor communicates, their approach to mentorship, and their communication style"
              rows={15}
              className="font-mono text-sm"
            />
            <p className="text-xs text-muted-foreground">
              The persona defines how your mentor will communicate and approach conversations. Be specific about their
              style, expertise, and how they provide guidance.
            </p>
          </div>
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={() => setOpen(false)}>
            Cancel
          </Button>
          <Button onClick={handleSave} disabled={updateMentorMutation.isPending}>
            {updateMentorMutation.isPending ? "Saving..." : "Save Changes"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
