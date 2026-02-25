"use client";

import Link from "next/link";
import { PageLayout } from "@/components/layout/page-layout";
import { useActiveAgents, useRecentAgents, useAgentStats } from "@/hooks/use-agents";
import { useAgentActivity } from "@/hooks/use-agent-activity";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Activity,
  Clock,
  DollarSign,
  Zap,
  CheckCircle,
  XCircle,
  Loader2,
  ArrowRight,
  Bot,
  FileText,
} from "lucide-react";
import { formatDistanceToNow } from "date-fns";
import { cn } from "@/lib/utils";

const statusColors: Record<string, string> = {
  idle: "bg-gray-500/10 text-gray-500 hover:bg-gray-500/20",
  starting: "bg-blue-500/10 text-blue-500 hover:bg-blue-500/20",
  processing: "bg-yellow-500/10 text-yellow-500 hover:bg-yellow-500/20",
  typing: "bg-purple-500/10 text-purple-500 hover:bg-purple-500/20",
  completed: "bg-green-500/10 text-green-500 hover:bg-green-500/20",
  error: "bg-red-500/10 text-red-500 hover:bg-red-500/20",
};

const statusIcons: Record<string, typeof Clock> = {
  idle: Clock,
  starting: Loader2,
  processing: Activity,
  typing: Zap,
  completed: CheckCircle,
  error: XCircle,
};

export default function AgentsPage() {
  const { data: activeData, isLoading: activeLoading } = useActiveAgents();
  const { data: recentData, isLoading: recentLoading } = useRecentAgents(20);
  const { data: stats } = useAgentStats();
  const { connected } = useAgentActivity();

  const activeSessions = activeData?.active_sessions || [];
  const recentSessions = recentData?.recent_sessions || [];

  const formatDuration = (seconds: number) => {
    if (seconds < 60) return `${seconds.toFixed(1)}s`;
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}m ${secs}s`;
  };

  const getEntityLink = (session: any) => {
    const type = session.entity_type;
    const id = session.entity_id;

    if (type === "project") return `/projects/${id}`;
    if (type === "issue") return `/issues/${id}`;
    if (type === "milestone") return `/milestones/${id}`;
    if (type === "initiative") return `/initiatives/${id}`;
    if (type === "mentor") return `/mentors/${id}`;

    return "#";
  };

  return (
    <PageLayout
      title="AI Agents"
      isLoading={activeLoading && recentLoading}
    >
      <div className="flex-1 p-6">
        {/* Connection Status */}
        <div className="mb-6 flex items-center justify-between">
          <p className="text-sm text-muted-foreground">
            Real-time monitoring of AI agent activity
          </p>
          <Badge variant={connected ? "default" : "destructive"} className="gap-1">
            <div className={cn("h-2 w-2 rounded-full", connected ? "bg-green-500" : "bg-red-500")} />
            {connected ? "Connected" : "Disconnected"}
          </Badge>
        </div>

        {/* Quick Navigation */}
        <div className="mb-6">
          <h2 className="mb-4 text-xl font-semibold">Agent Management</h2>
          <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
            <Link href="/agents/configured">
              <Card className="cursor-pointer transition-colors hover:border-primary/50 h-full">
                <CardContent className="pt-6">
                  <div className="flex items-start gap-4">
                    <div className="rounded-lg bg-primary/10 p-3">
                      <Bot className="h-6 w-6 text-primary" />
                    </div>
                    <div className="flex-1">
                      <h3 className="font-semibold mb-1">Configured Agents</h3>
                      <p className="text-sm text-muted-foreground mb-3">
                        View all configured AI agents with their capabilities, instructions, and available tools
                      </p>
                      <div className="flex items-center text-sm text-primary">
                        View Agents <ArrowRight className="ml-1 h-4 w-4" />
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </Link>

            <Link href="/agents/sessions">
              <Card className="cursor-pointer transition-colors hover:border-primary/50 h-full">
                <CardContent className="pt-6">
                  <div className="flex items-start gap-4">
                    <div className="rounded-lg bg-green-500/10 p-3">
                      <FileText className="h-6 w-6 text-green-500" />
                    </div>
                    <div className="flex-1">
                      <h3 className="font-semibold mb-1">Agent Sessions</h3>
                      <p className="text-sm text-muted-foreground mb-3">
                        Browse and filter all agent sessions with detailed metrics, filters, and search
                      </p>
                      <div className="flex items-center text-sm text-green-500">
                        View Sessions <ArrowRight className="ml-1 h-4 w-4" />
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </Link>
          </div>
        </div>

        {/* Stats Cards */}
        <div className="mb-6 grid grid-cols-1 gap-4 md:grid-cols-4">
          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div className="space-y-1">
                  <p className="text-sm text-muted-foreground">Active Agents</p>
                  <p className="text-2xl font-bold">{stats?.active_count || 0}</p>
                </div>
                <Activity className="h-8 w-8 text-blue-500" />
              </div>
            </CardContent>
          </Card>

          <Link href="/agents/sessions">
            <Card className="cursor-pointer transition-colors hover:border-primary/50">
              <CardContent className="pt-6">
                <div className="flex items-center justify-between">
                  <div className="space-y-1">
                    <p className="text-sm text-muted-foreground">Recent Sessions</p>
                    <p className="text-2xl font-bold">{stats?.recent_count || 0}</p>
                  </div>
                  <Clock className="h-8 w-8 text-green-500" />
                </div>
              </CardContent>
            </Card>
          </Link>

          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div className="space-y-1">
                  <p className="text-sm text-muted-foreground">Total Cost</p>
                  <p className="text-2xl font-bold">${(stats?.total_cost_usd || 0).toFixed(4)}</p>
                </div>
                <DollarSign className="h-8 w-8 text-yellow-500" />
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div className="space-y-1">
                  <p className="text-sm text-muted-foreground">Avg Duration</p>
                  <p className="text-2xl font-bold">{formatDuration(stats?.avg_duration_seconds || 0)}</p>
                </div>
                <Zap className="h-8 w-8 text-purple-500" />
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Active Sessions */}
        <div className="mb-6">
          <h2 className="mb-4 text-xl font-semibold">Active Sessions</h2>
          {activeSessions.length === 0 ? (
            <Card>
              <CardContent className="pt-6">
                <div className="py-12 text-center text-muted-foreground">
                  <Activity className="mx-auto mb-4 h-12 w-12 opacity-20" />
                  <p>No active agent sessions</p>
                </div>
              </CardContent>
            </Card>
          ) : (
            <div className="space-y-3">
              {activeSessions.map((session: any) => {
                const StatusIcon = statusIcons[session.status];
                return (
                  <Card key={session.session_id} className="cursor-pointer transition-colors hover:border-primary/50">
                    <CardContent className="pt-6">
                      <div className="flex items-start justify-between gap-4">
                        <div className="flex-1 space-y-2">
                          <div className="flex items-center gap-2">
                            <Badge
                              variant="secondary"
                              className={cn("text-xs", statusColors[session.status])}
                            >
                              <StatusIcon className={cn("mr-1 h-3 w-3", session.status === "starting" ? "animate-spin" : "")} />
                              {session.status.replace("_", " ")}
                            </Badge>
                            <Badge variant="outline" className="text-xs">
                              {session.entity_type}
                            </Badge>
                            <span className="text-xs text-muted-foreground">
                              Started {formatDistanceToNow(new Date(session.started_at))} ago
                            </span>
                          </div>
                          <Link
                            href={getEntityLink(session)}
                            className="font-medium text-blue-600 hover:text-blue-800"
                          >
                            {session.entity_title || session.entity_id}
                          </Link>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                );
              })}
            </div>
          )}
        </div>

        {/* Recent Sessions */}
        <div>
          <div className="mb-4 flex items-center justify-between">
            <h2 className="text-xl font-semibold">Recent Sessions</h2>
            <Link href="/agents/sessions">
              <Button variant="outline" size="sm">
                View All
                <ArrowRight className="ml-2 h-4 w-4" />
              </Button>
            </Link>
          </div>
          {recentSessions.length === 0 ? (
            <Card>
              <CardContent className="pt-6">
                <div className="py-12 text-center text-muted-foreground">
                  <Clock className="mx-auto mb-4 h-12 w-12 opacity-20" />
                  <p>No recent sessions</p>
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
                        <th className="px-4 py-3 text-left text-sm font-medium text-muted-foreground">Entity</th>
                        <th className="px-4 py-3 text-left text-sm font-medium text-muted-foreground">Duration</th>
                        <th className="px-4 py-3 text-left text-sm font-medium text-muted-foreground">Cost</th>
                        <th className="px-4 py-3 text-left text-sm font-medium text-muted-foreground">Completed</th>
                      </tr>
                    </thead>
                    <tbody>
                      {recentSessions.map((session: any) => {
                        const StatusIcon = statusIcons[session.status];
                        return (
                          <tr key={session.session_id} className="border-b last:border-0 hover:bg-muted/50">
                            <td className="px-4 py-3">
                              <Badge
                                variant="secondary"
                                className={cn("text-xs", statusColors[session.status])}
                              >
                                <StatusIcon className="mr-1 h-3 w-3" />
                                {session.status}
                              </Badge>
                            </td>
                            <td className="px-4 py-3">
                              <div className="space-y-1">
                                <Link
                                  href={getEntityLink(session)}
                                  className="text-sm font-medium text-blue-600 hover:text-blue-800"
                                >
                                  {session.entity_title || session.entity_id}
                                </Link>
                                <div className="text-xs capitalize text-muted-foreground">{session.entity_type}</div>
                              </div>
                            </td>
                            <td className="px-4 py-3 text-sm">{formatDuration(session.duration_seconds)}</td>
                            <td className="px-4 py-3 text-sm">${session.cost_usd.toFixed(4)}</td>
                            <td className="px-4 py-3 text-sm text-muted-foreground">
                              {formatDistanceToNow(new Date(session.completed_at || session.updated_at))} ago
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
