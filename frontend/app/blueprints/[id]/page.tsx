"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { PageLayout } from "@/components/layout/page-layout";
import { useBlueprint, useDeleteBlueprint } from "@/hooks/use-blueprints";
import { blueprintsApi } from "@/lib/api/blueprints";
import { EntityCommentsSection } from "@/components/shared/entity-comments-section";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { MoreVertical, Trash2, ArrowLeft, FileCode2 } from "lucide-react";
import { cn } from "@/lib/utils";
import { formatDistanceToNow } from "date-fns";
import { toast } from "sonner";
import type { BlueprintCategory, BlueprintSummary } from "@/lib/types";

const categoryColors: Record<BlueprintCategory, string> = {
  architecture: "bg-purple-500/10 text-purple-500",
  testing: "bg-green-500/10 text-green-500",
  styling: "bg-pink-500/10 text-pink-500",
  database: "bg-blue-500/10 text-blue-500",
  api: "bg-orange-500/10 text-orange-500",
  deployment: "bg-red-500/10 text-red-500",
  custom: "bg-gray-500/10 text-gray-500",
};

export default function BlueprintDetailPage() {
  const params = useParams();
  const router = useRouter();
  const blueprintId = params.id as string;

  const { data: blueprint, isLoading, error } = useBlueprint(blueprintId);
  const deleteBlueprint = useDeleteBlueprint();
  const [versions, setVersions] = useState<BlueprintSummary[]>([]);
  const [loadingVersions, setLoadingVersions] = useState(false);

  useEffect(() => {
    if (blueprint) {
      setLoadingVersions(true);
      blueprintsApi
        .getVersions(blueprint.name)
        .then(setVersions)
        .catch((err) => console.error("Failed to load versions:", err))
        .finally(() => setLoadingVersions(false));
    }
  }, [blueprint?.name]);

  const handleDelete = () => {
    if (!blueprint) return;
    if (!confirm(`Are you sure you want to delete the blueprint "${blueprint.name}"?`)) return;

    deleteBlueprint.mutate(blueprint.id, {
      onSuccess: () => {
        toast.success("Blueprint deleted successfully");
        router.push("/blueprints");
      },
      onError: (error) => {
        toast.error(error instanceof Error ? error.message : "Failed to delete blueprint");
      },
    });
  };

  const renderContent = (obj: any, depth = 0): JSX.Element => {
    if (obj === null || obj === undefined) {
      return <span className="text-muted-foreground italic">null</span>;
    }

    if (typeof obj === "string") {
      return <span className="text-foreground">{obj}</span>;
    }

    if (typeof obj === "number" || typeof obj === "boolean") {
      return <span className="text-blue-600 dark:text-blue-400">{String(obj)}</span>;
    }

    if (Array.isArray(obj)) {
      if (obj.length === 0) {
        return <span className="text-muted-foreground">[]</span>;
      }
      return (
        <ul className={cn("space-y-1 list-disc", depth > 0 && "ml-4")}>
          {obj.map((item, index) => (
            <li key={index} className="text-sm">
              {renderContent(item, depth + 1)}
            </li>
          ))}
        </ul>
      );
    }

    if (typeof obj === "object") {
      return (
        <div className={cn("space-y-3", depth > 0 && "ml-4 pl-4 border-l-2 border-border")}>
          {Object.entries(obj).map(([key, value]) => (
            <div key={key} className="space-y-1">
              <div className="font-semibold text-sm text-foreground">
                {key.replace(/_/g, " ").replace(/\b\w/g, (l) => l.toUpperCase())}:
              </div>
              <div className="text-sm">{renderContent(value, depth + 1)}</div>
            </div>
          ))}
        </div>
      );
    }

    return <span>{String(obj)}</span>;
  };

  // Early return if no blueprint data
  if (!blueprint) {
    return (
      <PageLayout
        title="Blueprint Not Found"
        isLoading={isLoading}
        error={error || new Error("Blueprint not found or failed to load")}
      >
        <div />
      </PageLayout>
    );
  }

  return (
    <PageLayout
      title={blueprint.name}
      isLoading={isLoading}
      error={error}
      headerChildren={
        <div className="flex items-center gap-2">
          <Button variant="ghost" size="sm" asChild>
            <Link href="/blueprints">
              <ArrowLeft className="mr-2 h-4 w-4" />
              Back
            </Link>
          </Button>

          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="ghost" size="icon">
                <MoreVertical className="h-4 w-4" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              <DropdownMenuItem onClick={handleDelete} className="text-destructive">
                <Trash2 className="mr-2 h-4 w-4" />
                Delete Blueprint
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      }
    >
      <div className="flex flex-col h-full overflow-hidden">
        {/* Scrollable Content Area */}
        <div className="flex-1 overflow-y-auto space-y-6 p-6 pb-0">
        {/* Header */}
        <div className="space-y-4">
          <div className="flex flex-wrap items-center gap-2">
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

          <p className="text-muted-foreground">{blueprint.description}</p>
        </div>

        <Separator />

        {/* Content Section */}
        <div className="grid gap-6 lg:grid-cols-3">
          {/* Main Content */}
          <div className="lg:col-span-2 space-y-6">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <FileCode2 className="h-5 w-5" />
                  Blueprint Content
                </CardTitle>
                <CardDescription>
                  Architectural patterns, rules, and best practices
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="rounded-lg bg-muted/50 p-4 max-h-[600px] overflow-y-auto">
                  {renderContent(blueprint.content)}
                </div>
              </CardContent>
            </Card>

            {/* Raw JSON View */}
            <Card>
              <CardHeader>
                <CardTitle>Raw JSON</CardTitle>
                <CardDescription>Copy and use this blueprint elsewhere</CardDescription>
              </CardHeader>
              <CardContent>
                <pre className="rounded-lg bg-muted p-4 text-xs overflow-x-auto max-h-96 overflow-y-auto">
                  <code>{JSON.stringify(blueprint.content, null, 2)}</code>
                </pre>
              </CardContent>
            </Card>
          </div>

          {/* Sidebar */}
          <div className="space-y-6">
            {/* Version Switcher */}
            {versions.length > 1 && (
              <Card>
                <CardHeader>
                  <CardTitle className="text-sm font-medium">Version</CardTitle>
                </CardHeader>
                <CardContent>
                  <Select
                    value={blueprint.id}
                    onValueChange={(value) => router.push(`/blueprints/${value}`)}
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {versions.map((v) => (
                        <SelectItem key={v.id} value={v.id}>
                          <div className="flex items-center gap-2">
                            <span>v{v.version}</span>
                            {v.is_active && (
                              <Badge variant="secondary" className="text-xs bg-green-500/10 text-green-500">
                                Active
                              </Badge>
                            )}
                          </div>
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </CardContent>
              </Card>
            )}

            {/* Metadata */}
            <Card>
              <CardHeader>
                <CardTitle className="text-sm font-medium">Metadata</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4 text-sm">
                <div>
                  <span className="font-medium">Category:</span>
                  <p className="capitalize text-muted-foreground">{blueprint.category}</p>
                </div>
                <div>
                  <span className="font-medium">Version:</span>
                  <p className="text-muted-foreground">{blueprint.version}</p>
                </div>
                <div>
                  <span className="font-medium">Status:</span>
                  <p className="text-muted-foreground">
                    {blueprint.is_active ? "Active" : "Inactive"}
                  </p>
                </div>
              </CardContent>
            </Card>

            {/* Timestamps */}
            <Card>
              <CardHeader>
                <CardTitle className="text-sm font-medium">Timeline</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4 text-sm">
                <div>
                  <span className="font-medium">Created:</span>
                  <p className="text-muted-foreground">
                    {formatDistanceToNow(new Date(blueprint.created_at))} ago
                  </p>
                </div>
                <div>
                  <span className="font-medium">Last updated:</span>
                  <p className="text-muted-foreground">
                    {formatDistanceToNow(new Date(blueprint.updated_at))} ago
                  </p>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
        </div>

        {/* Collapsible & Resizable Comments Section */}
        <EntityCommentsSection
          entityType="document"
          entityId={blueprintId}
          defaultHeight={450}
          minHeight={200}
          maxHeight={700}
          title="Comments"
        />
      </div>
    </PageLayout>
  );
}
