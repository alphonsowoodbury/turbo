"use client";

import { useParams, useRouter } from "next/navigation";
import { PageLayout } from "@/components/layout/page-layout";
import { useScriptRun } from "@/hooks/use-scripts";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  CheckCircle,
  XCircle,
  Loader2,
  Ban,
  ArrowLeft,
  Clock,
  Terminal,
  FileText,
  Database,
  Folder,
  User,
} from "lucide-react";
import { formatDistanceToNow } from "date-fns";
import { cn } from "@/lib/utils";

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

export default function ScriptRunDetailPage() {
  const params = useParams();
  const router = useRouter();
  const scriptRunId = params.id as string;
  const { data: scriptRun, isLoading } = useScriptRun(scriptRunId);

  const formatDuration = (seconds: number) => {
    if (seconds < 60) return `${seconds.toFixed(1)}s`;
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}m ${secs}s`;
  };

  if (isLoading || !scriptRun) {
    return (
      <PageLayout title="Script Run Details" isLoading={true}>
        <div className="flex-1 page-padding" />
      </PageLayout>
    );
  }

  const StatusIcon = statusIcons[scriptRun.status];

  return (
    <PageLayout title="Script Run Details" isLoading={false}>
      <div className="flex-1 page-padding">
        <div className="mb-6">
          <Button
            variant="ghost"
            onClick={() => router.push("/scripts")}
            className="mb-4"
          >
            <ArrowLeft className="mr-2 h-4 w-4" />
            Back to Scripts
          </Button>

          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-2xl font-bold">{scriptRun.script_name}</h2>
              <p className="text-sm text-muted-foreground">{scriptRun.script_path}</p>
            </div>
            <Badge
              variant="secondary"
              className={cn("text-sm", statusColors[scriptRun.status])}
            >
              <StatusIcon
                className={cn(
                  "mr-2 h-4 w-4",
                  scriptRun.status === "running" && "animate-spin"
                )}
              />
              {scriptRun.status}
            </Badge>
          </div>
        </div>

        {/* Stats Grid */}
        <div className="mb-6 grid grid-cols-1 gap-4 md:grid-cols-4">
          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div className="space-y-1">
                  <p className="text-sm text-muted-foreground">Duration</p>
                  <p className="text-xl font-bold">{formatDuration(scriptRun.duration_seconds)}</p>
                </div>
                <Clock className="h-8 w-8 text-purple-500" />
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div className="space-y-1">
                  <p className="text-sm text-muted-foreground">Files Processed</p>
                  <p className="text-xl font-bold">{scriptRun.files_processed}</p>
                </div>
                <Folder className="h-8 w-8 text-blue-500" />
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div className="space-y-1">
                  <p className="text-sm text-muted-foreground">Records Affected</p>
                  <p className="text-xl font-bold">{scriptRun.records_affected}</p>
                </div>
                <Database className="h-8 w-8 text-green-500" />
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div className="space-y-1">
                  <p className="text-sm text-muted-foreground">Exit Code</p>
                  <p className="text-xl font-bold">{scriptRun.exit_code ?? "N/A"}</p>
                </div>
                <Terminal className="h-8 w-8 text-orange-500" />
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Execution Details */}
        <div className="mb-6 grid grid-cols-1 gap-4 md:grid-cols-2">
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Execution Details</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              {scriptRun.command && (
                <div>
                  <p className="text-sm font-medium text-muted-foreground">Command</p>
                  <p className="mt-1 rounded bg-muted p-2 font-mono text-sm">{scriptRun.command}</p>
                </div>
              )}
              {scriptRun.arguments && (
                <div>
                  <p className="text-sm font-medium text-muted-foreground">Arguments</p>
                  <p className="mt-1 rounded bg-muted p-2 font-mono text-sm">{scriptRun.arguments}</p>
                </div>
              )}
              {scriptRun.triggered_by && (
                <div className="flex items-center gap-2">
                  <User className="h-4 w-4 text-muted-foreground" />
                  <span className="text-sm">
                    Triggered by: <span className="font-medium">{scriptRun.triggered_by}</span>
                  </span>
                </div>
              )}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="text-base">Timeline</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <div>
                <p className="text-sm font-medium text-muted-foreground">Started</p>
                <p className="mt-1 text-sm">
                  {new Date(scriptRun.started_at).toLocaleString()}
                  <span className="ml-2 text-muted-foreground">
                    ({formatDistanceToNow(new Date(scriptRun.started_at))} ago)
                  </span>
                </p>
              </div>
              {scriptRun.completed_at && (
                <div>
                  <p className="text-sm font-medium text-muted-foreground">Completed</p>
                  <p className="mt-1 text-sm">
                    {new Date(scriptRun.completed_at).toLocaleString()}
                    <span className="ml-2 text-muted-foreground">
                      ({formatDistanceToNow(new Date(scriptRun.completed_at))} ago)
                    </span>
                  </p>
                </div>
              )}
              <div>
                <p className="text-sm font-medium text-muted-foreground">Last Updated</p>
                <p className="mt-1 text-sm">
                  {new Date(scriptRun.updated_at).toLocaleString()}
                  <span className="ml-2 text-muted-foreground">
                    ({formatDistanceToNow(new Date(scriptRun.updated_at))} ago)
                  </span>
                </p>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Output */}
        {scriptRun.output && (
          <Card className="mb-6">
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-base">
                <FileText className="h-4 w-4" />
                Output
              </CardTitle>
            </CardHeader>
            <CardContent>
              <pre className="overflow-x-auto rounded bg-muted p-4 text-sm">
                {scriptRun.output}
              </pre>
            </CardContent>
          </Card>
        )}

        {/* Error */}
        {scriptRun.error && (
          <Card className="border-red-500/20">
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-base text-red-500">
                <XCircle className="h-4 w-4" />
                Error
              </CardTitle>
            </CardHeader>
            <CardContent>
              <pre className="overflow-x-auto rounded bg-red-500/10 p-4 text-sm text-red-500">
                {scriptRun.error}
              </pre>
            </CardContent>
          </Card>
        )}

        {/* ID for debugging */}
        <div className="mt-6 text-xs text-muted-foreground">
          Run ID: {scriptRun.id}
        </div>
      </div>
    </PageLayout>
  );
}
