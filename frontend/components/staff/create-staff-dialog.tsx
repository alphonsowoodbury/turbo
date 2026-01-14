"use client";

import { useState } from "react";
import { Plus, Award, Code, Shield, Target, Server, Lightbulb, Lock, Database } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { useCreateStaff } from "@/hooks/use-staff";
import { staffTemplates, type StaffTemplate } from "@/lib/staff-templates";
import { useRouter } from "next/navigation";

const iconMap: Record<string, any> = {
  target: Target,
  code: Code,
  shield: Shield,
  award: Award,
  server: Server,
  lightbulb: Lightbulb,
  lock: Lock,
  database: Database,
};

export function CreateStaffDialog() {
  const router = useRouter();
  const [isOpen, setIsOpen] = useState(false);
  const [selectedTemplate, setSelectedTemplate] = useState<StaffTemplate | null>(null);
  const [customizing, setCustomizing] = useState(false);

  // Form state
  const [name, setName] = useState("");
  const [handle, setHandle] = useState("");
  const [alias, setAlias] = useState("");
  const [roleType, setRoleType] = useState<"leadership" | "domain_expert">("domain_expert");
  const [roleTitle, setRoleTitle] = useState("");
  const [description, setDescription] = useState("");
  const [persona, setPersona] = useState("");

  const createStaff = useCreateStaff();

  const handleSelectTemplate = (template: StaffTemplate) => {
    setSelectedTemplate(template);
    setName(template.name);
    setHandle(template.handle);
    setAlias(template.alias);
    setRoleType(template.role_type);
    setRoleTitle(template.role_title);
    setDescription(template.description);
    setPersona(template.persona);
    setCustomizing(true);
  };

  const handleCreateFromTemplate = async () => {
    if (!selectedTemplate) return;

    try {
      const result = await createStaff.mutateAsync({
        name: selectedTemplate.name,
        handle: selectedTemplate.handle,
        alias: selectedTemplate.alias,
        role_type: selectedTemplate.role_type,
        role_title: selectedTemplate.role_title,
        description: selectedTemplate.description,
        persona: selectedTemplate.persona,
        monitoring_scope: {
          entity_types: [],
          tags: [],
          focus: "",
          metrics: [],
        },
        capabilities: selectedTemplate.capabilities || [],
        is_leadership_role: selectedTemplate.role_type === "leadership",
      });

      // Close dialog and navigate to chat
      setIsOpen(false);
      setSelectedTemplate(null);
      setCustomizing(false);
      resetForm();

      if (result?.id) {
        router.push(`/staff/${result.id}/chat`);
      }
    } catch (error) {
      console.error("Failed to create staff:", error);
      alert("Failed to create staff member. Please try again.");
    }
  };

  const handleCreateCustom = async () => {
    if (!name || !handle || !description || !persona) {
      alert("Please fill in all required fields");
      return;
    }

    try {
      const result = await createStaff.mutateAsync({
        name,
        handle,
        alias: alias || undefined,
        role_type: roleType,
        role_title: roleTitle || undefined,
        description,
        persona,
        monitoring_scope: {
          entity_types: [],
          tags: [],
          focus: "",
          metrics: [],
        },
        capabilities: [],
        is_leadership_role: roleType === "leadership",
      });

      setIsOpen(false);
      setCustomizing(false);
      resetForm();

      if (result?.id) {
        router.push(`/staff/${result.id}/chat`);
      }
    } catch (error) {
      console.error("Failed to create staff:", error);
      alert("Failed to create staff member. Please try again.");
    }
  };

  const resetForm = () => {
    setName("");
    setHandle("");
    setAlias("");
    setRoleType("domain_expert");
    setRoleTitle("");
    setDescription("");
    setPersona("");
    setSelectedTemplate(null);
  };

  const handleClose = () => {
    setIsOpen(false);
    setCustomizing(false);
    setSelectedTemplate(null);
    resetForm();
  };

  return (
    <Dialog open={isOpen} onOpenChange={(open) => {
      if (!open) handleClose();
      setIsOpen(open);
    }}>
      <DialogTrigger asChild>
        <Button>
          <Plus className="h-4 w-4 mr-2" />
          Create Staff
        </Button>
      </DialogTrigger>
      <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>Create AI Staff Member</DialogTitle>
          <DialogDescription>
            Choose a template or create a custom staff member
          </DialogDescription>
        </DialogHeader>

        {!customizing ? (
          <div>
            <h3 className="font-semibold mb-4">Choose a Template</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {staffTemplates.map((template) => {
                const Icon = iconMap[template.icon] || Target;
                return (
                  <Card
                    key={template.handle}
                    className="cursor-pointer hover:border-primary transition-colors"
                    onClick={() => handleSelectTemplate(template)}
                  >
                    <CardHeader>
                      <div className="flex items-start gap-3">
                        <div className="p-2 rounded-lg bg-primary/10">
                          <Icon className="h-5 w-5 text-primary" />
                        </div>
                        <div className="flex-1">
                          <CardTitle className="text-base">{template.name}</CardTitle>
                          <p className="text-xs text-muted-foreground mt-1">
                            @{template.alias} · {template.role_title}
                          </p>
                        </div>
                      </div>
                    </CardHeader>
                    <CardContent>
                      <p className="text-sm text-muted-foreground">
                        {template.description}
                      </p>
                    </CardContent>
                  </Card>
                );
              })}
            </div>

            <div className="mt-6">
              <Button
                variant="outline"
                onClick={() => setCustomizing(true)}
                className="w-full"
              >
                Or Create Custom Staff Member
              </Button>
            </div>
          </div>
        ) : (
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="name">Name *</Label>
                <Input
                  id="name"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="Senior Engineer AI"
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="handle">Handle * (unique)</Label>
                <Input
                  id="handle"
                  value={handle}
                  onChange={(e) => setHandle(e.target.value.toLowerCase().replace(/[^a-z0-9_]/g, '_'))}
                  placeholder="senior_engineer"
                />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="alias">Alias (short name for @mentions)</Label>
                <Input
                  id="alias"
                  value={alias}
                  onChange={(e) => setAlias(e.target.value)}
                  placeholder="SE"
                  maxLength={20}
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="role_type">Role Type</Label>
                <Select value={roleType} onValueChange={(v: any) => setRoleType(v)}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="domain_expert">Domain Expert</SelectItem>
                    <SelectItem value="leadership">Leadership</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>

            <div className="space-y-2">
              <Label htmlFor="role_title">Role Title</Label>
              <Input
                id="role_title"
                value={roleTitle}
                onChange={(e) => setRoleTitle(e.target.value)}
                placeholder="Senior Software Engineer"
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="description">Description *</Label>
              <Textarea
                id="description"
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                placeholder="Brief description of expertise and role..."
                rows={2}
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="persona">Persona * (How they should act and communicate)</Label>
              <Textarea
                id="persona"
                value={persona}
                onChange={(e) => setPersona(e.target.value)}
                placeholder="You are a Senior Software Engineer with expertise in... You help teams by... Communication style:..."
                rows={6}
              />
            </div>

            <DialogFooter>
              <Button variant="outline" onClick={() => {
                setCustomizing(false);
                setSelectedTemplate(null);
                resetForm();
              }}>
                Back to Templates
              </Button>
              <Button
                onClick={selectedTemplate ? handleCreateFromTemplate : handleCreateCustom}
                disabled={createStaff.isPending}
              >
                {createStaff.isPending ? "Creating..." : "Create & Start Chat"}
              </Button>
            </DialogFooter>
          </div>
        )}

        {!customizing && (
          <DialogFooter>
            <Button variant="outline" onClick={handleClose}>
              Cancel
            </Button>
          </DialogFooter>
        )}
      </DialogContent>
    </Dialog>
  );
}
