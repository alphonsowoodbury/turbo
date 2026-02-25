"use client";

import Link from "next/link";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import type { Project } from "@/lib/types";
import { formatDistanceToNow } from "date-fns";

interface ProjectCardProps {
  project: Project;
}

const priorityColors: Record<string, string> = {
  low: "bg-blue-500/10 text-blue-500 hover:bg-blue-500/20",
  medium: "bg-yellow-500/10 text-yellow-500 hover:bg-yellow-500/20",
  high: "bg-orange-500/10 text-orange-500 hover:bg-orange-500/20",
  critical: "bg-red-500/10 text-red-500 hover:bg-red-500/20",
};

const statusColors: Record<string, string> = {
  active: "bg-green-500/10 text-green-500 hover:bg-green-500/20",
  on_hold: "bg-yellow-500/10 text-yellow-500 hover:bg-yellow-500/20",
  completed: "bg-blue-500/10 text-blue-500 hover:bg-blue-500/20",
  archived: "bg-gray-500/10 text-gray-500 hover:bg-gray-500/20",
};

export function ProjectCard({ project }: ProjectCardProps) {
  return (
    <Link href={`/projects/${project.id}`}>
      <Card className="group transition-all hover:border-primary/50 hover:shadow-md">
        <CardHeader className="pb-3">
          <div className="flex items-start justify-between gap-4">
            <div className="flex-1">
              <h3 className="font-semibold leading-tight group-hover:text-primary">
                {project.name}
              </h3>
              <p className="mt-1 text-sm text-muted-foreground line-clamp-2">
                {project.description}
              </p>
            </div>
          </div>
        </CardHeader>

        <CardContent className="space-y-3">
          {/* Progress bar */}
          <div className="space-y-1">
            <div className="flex items-center justify-between text-xs">
              <span className="text-muted-foreground">Progress</span>
              <span className="font-medium">
                {project.completion_percentage}%
              </span>
            </div>
            <div className="h-1.5 w-full overflow-hidden rounded-full bg-secondary">
              <div
                className="h-full bg-primary transition-all"
                style={{ width: `${project.completion_percentage}%` }}
              />
            </div>
          </div>

          {/* Badges */}
          <div className="flex items-center gap-2">
            <Badge
              variant="secondary"
              className={cn(
                "text-xs",
                priorityColors[project.priority]
              )}
            >
              {project.priority}
            </Badge>
            <Badge
              variant="secondary"
              className={cn(
                "text-xs capitalize",
                statusColors[project.status]
              )}
            >
              {project.status.replace("_", " ")}
            </Badge>
          </div>

          {/* Metadata */}
          <div className="flex items-center justify-between text-xs text-muted-foreground">
            <span>
              Updated {formatDistanceToNow(new Date(project.updated_at))} ago
            </span>
          </div>
        </CardContent>
      </Card>
    </Link>
  );
}