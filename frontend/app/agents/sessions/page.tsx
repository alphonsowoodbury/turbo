"use client";

import { Suspense, useState, useMemo, useEffect } from "react";
import { useSearchParams } from "next/navigation";
import { PageLayout } from "@/components/layout/page-layout";
import { Card, CardContent } from "@/components/ui/card";
import { useRecentAgents } from "@/hooks/use-agents";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Filter, X, Clock, Zap, DollarSign, CheckCircle2, XCircle, AlertCircle, Bot } from "lucide-react";
import { cn } from "@/lib/utils";
import { formatDistanceToNow } from "date-fns";

interface AgentSession {
  session_id: string;
  entity_type: string;
  entity_id: string;
  entity_title?: string;
  status: string;
  error?: string;
  input_tokens: number;
  output_tokens: number;
  cost_usd: number;
  duration_seconds: number;
  comment_count: number;
  started_at: string;
  updated_at: string;
  completed_at?: string;
}

const getStatusIcon = (status: string) => {
  switch (status) {
    case "completed":
      return <CheckCircle2 className="h-4 w-4" />;
    case "error":
      return <XCircle className="h-4 w-4" />;
    default:
      return <AlertCircle className="h-4 w-4" />;
  }
};

const getStatusColor = (status: string) => {
  switch (status) {
    case "completed":
      return "default";
    case "error":
      return "destructive";
    case "typing":
      return "secondary";
    default:
      return "outline";
  }
};

const statusColors: Record<string, string> = {
  completed: "bg-green-500/10 text-green-500 hover:bg-green-500/20",
  error: "bg-red-500/10 text-red-500 hover:bg-red-500/20",
  typing: "bg-blue-500/10 text-blue-500 hover:bg-blue-500/20",
  processing: "bg-purple-500/10 text-purple-500 hover:bg-purple-500/20",
  starting: "bg-yellow-500/10 text-yellow-500 hover:bg-yellow-500/20",
};

function AgentSessionsContent() {
  const searchParams = useSearchParams();
  const agentFilter = searchParams.get("agent");

  const [showFilters, setShowFilters] = useState(false);
  const [selectedStatus, setSelectedStatus] = useState<string>("all");
  const [selectedEntityType, setSelectedEntityType] = useState<string>("all");
  const [selectedAgent, setSelectedAgent] = useState<string>("all");
  const [sortBy, setSortBy] = useState<string>("started");
  const [groupBy, setGroupBy] = useState<string>("none");

  const { data: sessionsData, isLoading } = useRecentAgents(1000);
  const sessions = sessionsData?.recent_sessions || [];

  // Set agent filter from URL on mount
  useEffect(() => {
    if (agentFilter) {
      setSelectedAgent(agentFilter);
      setShowFilters(true);
    }
  }, [agentFilter]);

  // Get unique agent names (extract from entity_title if present)
  const agentNames = useMemo(() => {
    const names = new Set<string>();
    sessions.forEach((s) => {
      // For now, we don't have agent name in sessions, so this will be empty
      // In the future, you can add agent_name to AgentSession model
    });
    return Array.from(names).sort();
  }, [sessions]);

  // Apply filters
  const filteredSessions = useMemo(() => {
    let filtered = [...sessions];

    if (selectedStatus !== "all") {
      filtered = filtered.filter((s) => s.status === selectedStatus);
    }

    if (selectedEntityType !== "all") {
      filtered = filtered.filter((s) => s.entity_type === selectedEntityType);
    }

    // Note: Agent filtering would require adding agent_name to the session data
    // For now, this filter is shown but doesn't filter anything

    return filtered;
  }, [sessions, selectedStatus, selectedEntityType, selectedAgent]);

  // Sort sessions
  const sortedSessions = useMemo(() => {
    const sorted = [...filteredSessions];

    switch (sortBy) {
      case "started":
        return sorted.sort((a, b) => new Date(b.started_at).getTime() - new Date(a.started_at).getTime());
      case "duration":
        return sorted.sort((a, b) => b.duration_seconds - a.duration_seconds);
      case "cost":
        return sorted.sort((a, b) => b.cost_usd - a.cost_usd);
      case "status":
        return sorted.sort((a, b) => a.status.localeCompare(b.status));
      default:
        return sorted;
    }
  }, [filteredSessions, sortBy]);

  // Group sessions
  const groupedSessions = useMemo(() => {
    if (groupBy === "none") {
      return { "All Sessions": sortedSessions };
    }

    const groups: Record<string, typeof sortedSessions> = {};

    sortedSessions.forEach((session) => {
      let key = "";

      if (groupBy === "status") {
        key = session.status;
      } else if (groupBy === "entity_type") {
        key = session.entity_type;
      } else if (groupBy === "date") {
        const date = new Date(session.started_at);
        key = date.toLocaleDateString("en-US", { year: "numeric", month: "long", day: "numeric" });
      }

      if (!groups[key]) {
        groups[key] = [];
      }
      groups[key].push(session);
    });

    return groups;
  }, [sortedSessions, groupBy]);

  // Get unique entity types for filter
  const entityTypes = useMemo(() => {
    const types = new Set(sessions.map((s) => s.entity_type));
    return Array.from(types).sort();
  }, [sessions]);

  const hasActiveFilters = selectedStatus !== "all" || selectedEntityType !== "all" || selectedAgent !== "all";

  const clearFilters = () => {
    setSelectedStatus("all");
    setSelectedEntityType("all");
    setSelectedAgent("all");
  };

  const formatDuration = (seconds: number) => {
    if (seconds < 60) return `${seconds.toFixed(1)}s`;
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = Math.round(seconds % 60);
    return `${minutes}m ${remainingSeconds}s`;
  };

  return (
    <PageLayout
      title="Agent Sessions"
      isLoading={isLoading}
    >
      <div className="p-6">
        {/* Agent Filter Badge */}
        {selectedAgent !== "all" && (
          <div className="mb-4">
            <Badge variant="secondary" className="gap-2">
              <Bot className="h-3 w-3" />
              Filtering by: {selectedAgent}
              <button
                onClick={() => setSelectedAgent("all")}
                className="ml-1 hover:text-destructive"
              >
                <X className="h-3 w-3" />
              </button>
            </Badge>
          </div>
        )}

        {/* Controls Bar */}
        <div className="mb-4 flex items-center justify-between">
          <div className="text-sm text-muted-foreground">
            {sessions.length} total sessions
          </div>
          <div className="flex items-center gap-2">
            <Button
              variant={showFilters ? "secondary" : "outline"}
              size="sm"
              onClick={() => setShowFilters(!showFilters)}
            >
              <Filter className="h-4 w-4 mr-2" />
              Filter
              {hasActiveFilters && (
                <Badge variant="secondary" className="ml-2 h-4 px-1 text-[10px]">
                  {[selectedStatus !== "all", selectedEntityType !== "all", selectedAgent !== "all"].filter(Boolean).length}
                </Badge>
              )}
            </Button>
            {hasActiveFilters && (
              <Button variant="ghost" size="sm" onClick={clearFilters}>
                <X className="h-4 w-4 mr-1" />
                Clear
              </Button>
            )}
            <span className="text-sm text-muted-foreground">Sort:</span>
            <Select value={sortBy} onValueChange={setSortBy}>
              <SelectTrigger className="w-32 h-8">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="started">Started</SelectItem>
                <SelectItem value="duration">Duration</SelectItem>
                <SelectItem value="cost">Cost</SelectItem>
                <SelectItem value="status">Status</SelectItem>
              </SelectContent>
            </Select>
            <span className="text-sm text-muted-foreground">Group:</span>
            <Select value={groupBy} onValueChange={setGroupBy}>
              <SelectTrigger className="w-32 h-8">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="none">None</SelectItem>
                <SelectItem value="status">Status</SelectItem>
                <SelectItem value="entity_type">Entity Type</SelectItem>
                <SelectItem value="date">Date</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </div>

        {/* Filter Controls */}
        {showFilters && (
          <Card className="mb-4">
            <CardContent className="pt-6">
              <div className="grid grid-cols-3 gap-4">
                <div className="space-y-2">
                  <label className="text-sm font-medium">Status</label>
                  <Select value={selectedStatus} onValueChange={setSelectedStatus}>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="all">All Statuses</SelectItem>
                      <SelectItem value="completed">Completed</SelectItem>
                      <SelectItem value="error">Error</SelectItem>
                      <SelectItem value="typing">Typing</SelectItem>
                      <SelectItem value="processing">Processing</SelectItem>
                      <SelectItem value="starting">Starting</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                <div className="space-y-2">
                  <label className="text-sm font-medium">Entity Type</label>
                  <Select value={selectedEntityType} onValueChange={setSelectedEntityType}>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="all">All Types</SelectItem>
                      {entityTypes.map((type) => (
                        <SelectItem key={type} value={type}>
                          {type.charAt(0).toUpperCase() + type.slice(1)}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>

                <div className="space-y-2">
                  <label className="text-sm font-medium">Agent</label>
                  <Select value={selectedAgent} onValueChange={setSelectedAgent}>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="all">All Agents</SelectItem>
                      <SelectItem value="issue-triager">Issue Triager</SelectItem>
                      <SelectItem value="project-manager">Project Manager</SelectItem>
                      <SelectItem value="doc-curator">Doc Curator</SelectItem>
                      <SelectItem value="task-scheduler">Task Scheduler</SelectItem>
                      <SelectItem value="knowledge-connector">Knowledge Connector</SelectItem>
                      <SelectItem value="learning-curator">Learning Curator</SelectItem>
                      <SelectItem value="meeting-facilitator">Meeting Facilitator</SelectItem>
                      <SelectItem value="discovery-guide">Discovery Guide</SelectItem>
                      <SelectItem value="blueprint-architect">Blueprint Architect</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Sessions List */}
        {sortedSessions.length > 0 ? (
          <div className="space-y-6">
            {Object.entries(groupedSessions).map(([groupName, groupSessions]) => (
              <div key={groupName}>
                {groupBy !== "none" && (
                  <h3 className="mb-3 text-sm font-semibold text-muted-foreground capitalize">
                    {groupName} ({groupSessions.length})
                  </h3>
                )}
                <div className="space-y-3">
                  {groupSessions.map((session: AgentSession) => (
                    <Card key={session.session_id} className="hover:border-primary/50 cursor-pointer transition-colors">
                      <CardContent className="pt-6">
                        <div className="flex items-start justify-between gap-4">
                          <div className="flex-1 space-y-1">
                            <div className="flex items-center gap-2">
                              <h3 className="font-semibold">
                                {session.entity_title || `${session.entity_type} ${session.entity_id.slice(0, 8)}`}
                              </h3>
                            </div>
                            {session.error && (
                              <p className="text-sm text-destructive">{session.error}</p>
                            )}
                            <div className="flex items-center gap-2 text-xs text-muted-foreground">
                              <span>
                                Started {formatDistanceToNow(new Date(session.started_at))} ago
                              </span>
                              {session.duration_seconds > 0 && (
                                <>
                                  <span>•</span>
                                  <span className="flex items-center gap-1">
                                    <Zap className="h-3 w-3" />
                                    {formatDuration(session.duration_seconds)}
                                  </span>
                                </>
                              )}
                              {session.cost_usd > 0 && (
                                <>
                                  <span>•</span>
                                  <span className="flex items-center gap-1">
                                    <DollarSign className="h-3 w-3" />
                                    ${session.cost_usd.toFixed(4)}
                                  </span>
                                </>
                              )}
                              <span>•</span>
                              <span>
                                {(session.input_tokens + session.output_tokens).toLocaleString()} tokens
                              </span>
                            </div>
                          </div>
                          <div className="flex gap-2">
                            <Badge variant="outline" className="text-xs capitalize">
                              {session.entity_type}
                            </Badge>
                            <Badge
                              variant="secondary"
                              className={cn(
                                "text-xs capitalize gap-1",
                                statusColors[session.status]
                              )}
                            >
                              {getStatusIcon(session.status)}
                              {session.status}
                            </Badge>
                          </div>
                        </div>
                      </CardContent>
                    </Card>
                  ))}
                </div>
              </div>
            ))}

            {/* Summary */}
            <div className="pt-6 border-t">
              <div className="flex items-center justify-between text-sm text-muted-foreground">
                <span>
                  Showing {sortedSessions.length} of {sessions.length} sessions
                </span>
                <span>
                  Total cost: ${sortedSessions.reduce((sum, s) => sum + s.cost_usd, 0).toFixed(4)}
                </span>
              </div>
            </div>
          </div>
        ) : (
          <div className="flex h-64 items-center justify-center">
            <div className="text-center">
              <AlertCircle className="h-16 w-16 mx-auto mb-4 opacity-20" />
              <p className="text-sm text-muted-foreground">
                {sessions && sessions.length > 0
                  ? "No sessions match the current filters."
                  : "No agent sessions found."}
              </p>
              {hasActiveFilters && sessions && sessions.length > 0 && (
                <Button
                  variant="outline"
                  size="sm"
                  className="mt-4"
                  onClick={clearFilters}
                >
                  Clear Filters
                </Button>
              )}
            </div>
          </div>
        )}
      </div>
    </PageLayout>
  );
}

export default function AgentSessionsPage() {
  return (
    <Suspense fallback={
      <PageLayout title="Agent Sessions" isLoading={true}>
        <div className="p-6">
          <div className="flex h-64 items-center justify-center">
            <div className="text-sm text-muted-foreground">Loading sessions...</div>
          </div>
        </div>
      </PageLayout>
    }>
      <AgentSessionsContent />
    </Suspense>
  );
}
