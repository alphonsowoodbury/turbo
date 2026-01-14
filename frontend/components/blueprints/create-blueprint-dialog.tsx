"use client";

import { useState } from "react";
import { useCreateBlueprint } from "@/hooks/use-blueprints";
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
import type { BlueprintCategory } from "@/lib/types";

interface CreateBlueprintDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function CreateBlueprintDialog({ open, onOpenChange }: CreateBlueprintDialogProps) {
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [category, setCategory] = useState<BlueprintCategory>("architecture");
  const [version, setVersion] = useState("");
  const [isActive, setIsActive] = useState(true);
  const [contentJson, setContentJson] = useState("{}");

  const createBlueprint = useCreateBlueprint();

  const resetForm = () => {
    setName("");
    setDescription("");
    setCategory("architecture");
    setVersion("");
    setIsActive(true);
    setContentJson("{}");
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    // Validate JSON content
    let content: Record<string, any>;
    try {
      content = JSON.parse(contentJson);
    } catch (error) {
      toast.error("Invalid JSON in content field");
      return;
    }

    createBlueprint.mutate(
      {
        name,
        description,
        category,
        content,
        version: version || null,
        is_active: isActive,
      },
      {
        onSuccess: () => {
          toast.success("Blueprint created successfully");
          resetForm();
          onOpenChange(false);
        },
        onError: (error) => {
          toast.error(error instanceof Error ? error.message : "Failed to create blueprint");
        },
      }
    );
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>Create New Blueprint</DialogTitle>
          <DialogDescription>
            Define architectural standards and patterns for your projects.
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={handleSubmit}>
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label htmlFor="name">Name *</Label>
              <Input
                id="name"
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="e.g., Clean Architecture Pattern"
                required
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="description">Description *</Label>
              <Textarea
                id="description"
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                placeholder="Describe what this blueprint defines and when to use it..."
                rows={3}
                required
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="category">Category *</Label>
                <Select value={category} onValueChange={(value) => setCategory(value as BlueprintCategory)}>
                  <SelectTrigger id="category">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="architecture">Architecture</SelectItem>
                    <SelectItem value="testing">Testing</SelectItem>
                    <SelectItem value="styling">Styling</SelectItem>
                    <SelectItem value="database">Database</SelectItem>
                    <SelectItem value="api">API</SelectItem>
                    <SelectItem value="deployment">Deployment</SelectItem>
                    <SelectItem value="custom">Custom</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-2">
                <Label htmlFor="version">Version (optional)</Label>
                <Input
                  id="version"
                  value={version}
                  onChange={(e) => setVersion(e.target.value)}
                  placeholder="e.g., 1.0.0"
                />
              </div>
            </div>

            <div className="space-y-2">
              <Label htmlFor="content">Content (JSON) *</Label>
              <Textarea
                id="content"
                value={contentJson}
                onChange={(e) => setContentJson(e.target.value)}
                placeholder={`{
  "patterns": ["Repository", "Service Layer"],
  "rules": ["Use dependency injection", "Separate concerns"],
  "examples": {...}
}`}
                rows={8}
                className="font-mono text-sm"
                required
              />
              <p className="text-xs text-muted-foreground">
                Define patterns, standards, rules, and templates in JSON format.
              </p>
            </div>

            <div className="flex items-center space-x-2">
              <Switch id="is_active" checked={isActive} onCheckedChange={setIsActive} />
              <Label htmlFor="is_active" className="cursor-pointer">
                Active (can be used in projects)
              </Label>
            </div>
          </div>

          <DialogFooter>
            <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>
              Cancel
            </Button>
            <Button type="submit" disabled={createBlueprint.isPending}>
              {createBlueprint.isPending ? "Creating..." : "Create Blueprint"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
