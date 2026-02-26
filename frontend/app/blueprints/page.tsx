"use client";

import { useState } from "react";
import Link from "next/link";
import { PageLayout } from "@/components/layout/page-layout";
import { useBlueprints, useDeleteBlueprint } from "@/hooks/use-blueprints";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Loader2, MoreVertical, Plus, Trash2, FileCode2 } from "lucide-react";
import { cn } from "@/lib/utils";
import { toast } from "sonner";
import type { BlueprintCategory } from "@/lib/types";
import { CreateBlueprintDialog } from "@/components/blueprints/create-blueprint-dialog";

const categoryColors: Record<BlueprintCategory, string> = {
  architecture: "bg-purple-500/10 text-purple-500",
  testing: "bg-green-500/10 text-green-500",
  styling: "bg-pink-500/10 text-pink-500",
  database: "bg-blue-500/10 text-blue-500",
  api: "bg-orange-500/10 text-orange-500",
  deployment: "bg-red-500/10 text-red-500",
  custom: "bg-gray-500/10 text-gray-500",
};

export default function BlueprintsPage() {
  const [categoryFilter, setCategoryFilter] = useState<BlueprintCategory | "all">("all");
  const [activeFilter, setActiveFilter] = useState<boolean | "all">(true);
  const [createDialogOpen, setCreateDialogOpen] = useState(false);

  const { data: blueprints, isLoading } = useBlueprints(
    categoryFilter === "all" && activeFilter === "all"
      ? undefined
      : {
          ...(categoryFilter !== "all" && { category: categoryFilter }),
          ...(activeFilter !== "all" && { is_active: activeFilter }),
        }
  );

  const deleteBlueprint = useDeleteBlueprint();

  const handleDelete = (id: string, name: string) => {
    if (!confirm(`Are you sure you want to delete the blueprint "${name}"?`)) return;

    deleteBlueprint.mutate(id, {
      onSuccess: () => {
        toast.success("Blueprint deleted successfully");
      },
      onError: (error) => {
        toast.error(error instanceof Error ? error.message : "Failed to delete blueprint");
      },
    });
  };

  return (
    <PageLayout
      title="Blueprints"
      isLoading={isLoading}
    >
      <div className="space-y-6 page-padding">
        {/* Header Button */}
        <div className="flex justify-end">
          <Button onClick={() => setCreateDialogOpen(true)}>
            <Plus className="mr-2 h-4 w-4" />
            New Blueprint
          </Button>
        </div>
        {/* Filters */}
        <div className="flex gap-4">
          <Select
            value={categoryFilter}
            onValueChange={(value) => setCategoryFilter(value as BlueprintCategory | "all")}
          >
            <SelectTrigger className="w-[200px]">
              <SelectValue placeholder="Filter by category" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Categories</SelectItem>
              <SelectItem value="architecture">Architecture</SelectItem>
              <SelectItem value="testing">Testing</SelectItem>
              <SelectItem value="styling">Styling</SelectItem>
              <SelectItem value="database">Database</SelectItem>
              <SelectItem value="api">API</SelectItem>
              <SelectItem value="deployment">Deployment</SelectItem>
              <SelectItem value="custom">Custom</SelectItem>
            </SelectContent>
          </Select>

          <Select
            value={activeFilter.toString()}
            onValueChange={(value) =>
              setActiveFilter(value === "all" ? "all" : value === "true")
            }
          >
            <SelectTrigger className="w-[200px]">
              <SelectValue placeholder="Filter by status" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Blueprints</SelectItem>
              <SelectItem value="true">Active Only</SelectItem>
              <SelectItem value="false">Inactive Only</SelectItem>
            </SelectContent>
          </Select>
        </div>

        {/* Blueprint Grid */}
        {blueprints && blueprints.length > 0 ? (
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {blueprints.map((blueprint) => (
              <Link key={blueprint.id} href={`/blueprints/${blueprint.id}`}>
                <Card className="relative cursor-pointer transition-colors hover:bg-accent">
                  <CardHeader>
                    <div className="flex items-start justify-between">
                      <div className="flex items-center gap-2">
                        <FileCode2 className="h-5 w-5 text-muted-foreground" />
                        <CardTitle className="text-lg">{blueprint.name}</CardTitle>
                      </div>
                      <DropdownMenu>
                        <DropdownMenuTrigger asChild>
                          <Button
                            variant="ghost"
                            size="icon"
                            className="h-8 w-8"
                            onClick={(e) => e.preventDefault()}
                          >
                            <MoreVertical className="h-4 w-4" />
                          </Button>
                        </DropdownMenuTrigger>
                        <DropdownMenuContent align="end">
                          <DropdownMenuItem
                            onClick={(e) => {
                              e.preventDefault();
                              handleDelete(blueprint.id, blueprint.name);
                            }}
                            className="text-destructive"
                          >
                            <Trash2 className="mr-2 h-4 w-4" />
                            Delete
                          </DropdownMenuItem>
                        </DropdownMenuContent>
                      </DropdownMenu>
                    </div>
                    <div className="flex items-center gap-2">
                      <Badge
                        variant="secondary"
                        className={cn("text-xs capitalize", categoryColors[blueprint.category])}
                      >
                        {blueprint.category}
                      </Badge>
                      {!blueprint.is_active && (
                        <Badge variant="secondary" className="text-xs bg-gray-500/10 text-gray-500">
                          Inactive
                        </Badge>
                      )}
                      {blueprint.version && (
                        <Badge variant="outline" className="text-xs">
                          v{blueprint.version}
                        </Badge>
                      )}
                    </div>
                  </CardHeader>
                </Card>
              </Link>
            ))}
          </div>
        ) : (
          <div className="flex h-64 items-center justify-center">
            <div className="text-center">
              <FileCode2 className="mx-auto h-12 w-12 text-muted-foreground/50" />
              <p className="mt-4 text-sm text-muted-foreground">
                No blueprints found. Create your first blueprint to get started.
              </p>
              <Button className="mt-4" onClick={() => setCreateDialogOpen(true)}>
                <Plus className="mr-2 h-4 w-4" />
                Create Blueprint
              </Button>
            </div>
          </div>
        )}
      </div>

      <CreateBlueprintDialog open={createDialogOpen} onOpenChange={setCreateDialogOpen} />
    </PageLayout>
  );
}
