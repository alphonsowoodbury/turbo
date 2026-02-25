"use client";

import { useRouter } from "next/navigation";
import { PageLayout } from "@/components/layout/page-layout";
import { useRunningScripts, useRecentScripts } from "@/hooks/use-scripts";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
  Activity,
  Clock,
  FileText,
  CheckCircle,
  XCircle,
  Loader2,
  Ban,
  Database,
  Folder,
} from "lucide-react";
import { formatDistanceToNow } from "date-fns";
import { cn } from "@/lib/utils";
import type { ScriptRun } from "@/lib/api/scripts";

const statusColors: Record<string, string> = {
  running: "bg-blue-500/10 text-blue-500 hover:bg-blue-500/20",
  completed: "bg-green-500/10 text-green-500 hover:bg-green-500/20",
  failed: "bg-red-500/10 text-red-500 hover:bg-red-500/20",
  cancelled: "bg-gray-500/10 text-gray-500 hover:bg-gray-500/20",
};

const statusIcons: Record<string, typeof Loader2> = {
  running: Loader2,
  completed: CheckCircle,
  failed: XCircle,
  cancelled: Ban,
};

export default function ScriptsPage() {
  const router = useRouter();
  const { data: runningScripts, isLoading: runningLoading } = useRunningScripts();
  const { data: recentScripts, isLoading: recentLoading } = useRecentScripts(50);

  const formatDuration = (seconds: number) => {
    if (seconds < 60) return `${seconds.toFixed(1)}s`;
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}m ${secs}s`;
  };

  // Calculate stats
  const totalCompleted = recentScripts?.filter((s: ScriptRun) => s.status === "completed").length || 0;
  const totalFailed = recentScripts?.filter((s: ScriptRun) => s.status === "failed").length || 0;
  const avgDuration = recentScripts?.length
    ? recentScripts.reduce((sum: number, s: ScriptRun) => sum + s.duration_seconds, 0) / recentScripts.length
    : 0;
  const totalFilesProcessed = recentScripts?.reduce((sum: number, s: ScriptRun) => sum + s.files_processed, 0) || 0;

  return (
    <PageLayout
      title="Python Scripts"
      isLoading={runningLoading && recentLoading}
    >
      <div className="flex-1 p-6">
        <div className="mb-6">
          <p className="text-sm text-muted-foreground">
            Monitor Python script executions and track their performance
          </p>
        </div>

        {/* Stats Cards */}
        <div className="mb-6 grid grid-cols-1 gap-4 md:grid-cols-4">
          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div className="space-y-1">
                  <p className="text-sm text-muted-foreground">Running</p>
                  <p className="text-2xl font-bold">{runningScripts?.length || 0}</p>
                </div>
                <Loader2 className={cn("h-8 w-8 text-blue-500", (runningScripts?.length || 0) > 0 && "animate-spin")} />
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div className="space-y-1">
                  <p className="text-sm text-muted-foreground">Completed</p>
                  <p className="text-2xl font-bold">{totalCompleted}</p>
                </div>
                <CheckCircle className="h-8 w-8 text-green-500" />
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div className="space-y-1">
                  <p className="text-sm text-muted-foreground">Failed</p>
                  <p className="text-2xl font-bold">{totalFailed}</p>
                </div>
                <XCircle className="h-8 w-8 text-red-500" />
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div className="space-y-1">
                  <p className="text-sm text-muted-foreground">Avg Duration</p>
                  <p className="text-2xl font-bold">{formatDuration(avgDuration)}</p>
                </div>
                <Clock className="h-8 w-8 text-purple-500" />
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Running Scripts */}
        {(runningScripts?.length || 0) > 0 && (
          <div className="mb-6">
            <h2 className="mb-4 text-xl font-semibold">Running Scripts</h2>
            <div className="space-y-3">
              {runningScripts?.map((script: ScriptRun) => {
                const StatusIcon = statusIcons[script.status];
                return (
                  <Card
                    key={script.id}
                    className="cursor-pointer transition-colors hover:border-primary/50"
                    onClick={() => router.push(`/scripts/${script.id}`)}
                  >
                    <CardContent className="pt-6">
                      <div className="flex items-start justify-between gap-4">
                        <div className="flex-1 space-y-2">
                          <div className="flex items-center gap-2">
                            <Badge
                              variant="secondary"
                              className={cn("text-xs", statusColors[script.status])}
                            >
                              <StatusIcon className="mr-1 h-3 w-3 animate-spin" />
                              {script.status}
                            </Badge>
                            <span className="text-xs text-muted-foreground">
                              Started {formatDistanceToNow(new Date(script.started_at))} ago
                            </span>
                          </div>
                          <div className="font-medium">{script.script_name}</div>
                          <div className="text-sm text-muted-foreground">{script.script_path}</div>
                          {script.triggered_by && (
                            <div className="text-xs text-muted-foreground">
                              Triggered by: {script.triggered_by}
                            </div>
                          )}
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                );
              })}
            </div>
          </div>
        )}

        {/* Recent Scripts */}
        <div>
          <h2 className="mb-4 text-xl font-semibold">Recent Scripts</h2>
          {!recentScripts || recentScripts.length === 0 ? (
            <Card>
              <CardContent className="pt-6">
                <div className="py-12 text-center text-muted-foreground">
                  <Activity className="mx-auto mb-4 h-12 w-12 opacity-20" />
                  <p>No script runs yet</p>
                </div>
              </CardContent>
            </Card>
          ) : (
            <Card>
              <CardContent className="pt-6">
                <div className="overflow-x-auto">
                  <table className="w-full">
                    <thead>
                      <tr className="border-b">
                        <th className="px-4 py-3 text-left text-sm font-medium text-muted-foreground">Status</th>
                        <th className="px-4 py-3 text-left text-sm font-medium text-muted-foreground">Script</th>
                        <th className="px-4 py-3 text-left text-sm font-medium text-muted-foreground">Duration</th>
                        <th className="px-4 py-3 text-left text-sm font-medium text-muted-foreground">Files</th>
                        <th className="px-4 py-3 text-left text-sm font-medium text-muted-foreground">Records</th>
                        <th className="px-4 py-3 text-left text-sm font-medium text-muted-foreground">Time</th>
                      </tr>
                    </thead>
                    <tbody>
                      {recentScripts.map((script: ScriptRun) => {
                        const StatusIcon = statusIcons[script.status];
                        return (
                          <tr
                            key={script.id}
                            className="border-b last:border-0 hover:bg-muted/50 cursor-pointer"
                            onClick={() => router.push(`/scripts/${script.id}`)}
                          >
                            <td className="px-4 py-3">
                              <Badge
                                variant="secondary"
                                className={cn("text-xs", statusColors[script.status])}
                              >
                                <StatusIcon className={cn("mr-1 h-3 w-3", script.status === "running" && "animate-spin")} />
                                {script.status}
                              </Badge>
                            </td>
                            <td className="px-4 py-3">
                              <div className="space-y-1">
                                <div className="text-sm font-medium">{script.script_name}</div>
                                <div className="text-xs text-muted-foreground">{script.script_path}</div>
                                {script.triggered_by && (
                                  <div className="text-xs text-muted-foreground">
                                    by {script.triggered_by}
                                  </div>
                                )}
                              </div>
                            </td>
                            <td className="px-4 py-3 text-sm">{formatDuration(script.duration_seconds)}</td>
                            <td className="px-4 py-3">
                              <div className="flex items-center gap-1 text-sm">
                                <Folder className="h-4 w-4 text-muted-foreground" />
                                {script.files_processed}
                              </div>
                            </td>
                            <td className="px-4 py-3">
                              <div className="flex items-center gap-1 text-sm">
                                <Database className="h-4 w-4 text-muted-foreground" />
                                {script.records_affected}
                              </div>
                            </td>
                            <td className="px-4 py-3 text-sm text-muted-foreground">
                              {formatDistanceToNow(new Date(script.completed_at || script.updated_at))} ago
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              </CardContent>
            </Card>
          )}
        </div>
      </div>
    </PageLayout>
  );
}
