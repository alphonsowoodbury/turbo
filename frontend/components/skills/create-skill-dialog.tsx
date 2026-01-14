"use client";

import { useState } from "react";
import { useCreateSkill } from "@/hooks/use-skills";
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
import { Switch } from "@/components/ui/switch";
import { toast } from "sonner";
import type { SkillCategory, ProficiencyLevel } from "@/lib/types";

interface CreateSkillDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function CreateSkillDialog({
  open,
  onOpenChange,
}: CreateSkillDialogProps) {
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [category, setCategory] = useState<SkillCategory>("technical");
  const [proficiencyLevel, setProficiencyLevel] = useState<ProficiencyLevel>("intermediate");
  const [yearsOfExperience, setYearsOfExperience] = useState("");
  const [isEndorsed, setIsEndorsed] = useState(false);

  const createSkill = useCreateSkill();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    // Validate required fields
    if (!name.trim()) {
      toast.error("Please enter a skill name");
      return;
    }

    createSkill.mutate(
      {
        name: name.trim(),
        description: description.trim() || null,
        category,
        proficiency_level: proficiencyLevel,
        years_of_experience: yearsOfExperience ? parseInt(yearsOfExperience) : null,
        is_endorsed: isEndorsed,
        last_used_at: null,
      },
      {
        onSuccess: () => {
          toast.success("Skill created successfully!");
          setName("");
          setDescription("");
          setCategory("technical");
          setProficiencyLevel("intermediate");
          setYearsOfExperience("");
          setIsEndorsed(false);
          onOpenChange(false);
        },
        onError: (error) => {
          toast.error(
            error instanceof Error ? error.message : "Failed to create skill"
          );
        },
      }
    );
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[525px]">
        <form onSubmit={handleSubmit}>
          <DialogHeader>
            <DialogTitle>Add New Skill</DialogTitle>
            <DialogDescription>
              Add a professional skill to your profile. Include details about your expertise level.
            </DialogDescription>
          </DialogHeader>

          <div className="grid gap-4 py-4">
            <div className="grid gap-2">
              <Label htmlFor="name">
                Skill Name <span className="text-destructive">*</span>
              </Label>
              <Input
                id="name"
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="e.g., React, Python, Project Management"
                required
              />
            </div>

            <div className="grid gap-2">
              <Label htmlFor="description">Description</Label>
              <Textarea
                id="description"
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                placeholder="Add notes about your experience with this skill..."
                rows={3}
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="grid gap-2">
                <Label htmlFor="category">Category</Label>
                <Select
                  value={category}
                  onValueChange={(value) => setCategory(value as SkillCategory)}
                >
                  <SelectTrigger id="category">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="technical">Technical</SelectItem>
                    <SelectItem value="soft_skills">Soft Skills</SelectItem>
                    <SelectItem value="tools">Tools</SelectItem>
                    <SelectItem value="languages">Languages</SelectItem>
                    <SelectItem value="certifications">Certifications</SelectItem>
                    <SelectItem value="other">Other</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div className="grid gap-2">
                <Label htmlFor="proficiency">Proficiency Level</Label>
                <Select
                  value={proficiencyLevel}
                  onValueChange={(value) => setProficiencyLevel(value as ProficiencyLevel)}
                >
                  <SelectTrigger id="proficiency">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="beginner">Beginner</SelectItem>
                    <SelectItem value="intermediate">Intermediate</SelectItem>
                    <SelectItem value="advanced">Advanced</SelectItem>
                    <SelectItem value="expert">Expert</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>

            <div className="grid gap-2">
              <Label htmlFor="years">Years of Experience</Label>
              <Input
                id="years"
                type="number"
                min="0"
                max="100"
                value={yearsOfExperience}
                onChange={(e) => setYearsOfExperience(e.target.value)}
                placeholder="Optional"
              />
            </div>

            <div className="flex items-center justify-between">
              <Label htmlFor="endorsed" className="text-base">Endorsed</Label>
              <Switch
                id="endorsed"
                checked={isEndorsed}
                onCheckedChange={setIsEndorsed}
              />
            </div>
          </div>

          <DialogFooter>
            <Button
              type="button"
              variant="outline"
              onClick={() => onOpenChange(false)}
            >
              Cancel
            </Button>
            <Button type="submit" disabled={createSkill.isPending}>
              {createSkill.isPending ? "Adding..." : "Add Skill"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
