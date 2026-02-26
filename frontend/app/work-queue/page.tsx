"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import {
  DndContext,
  closestCenter,
  KeyboardSensor,
  PointerSensor,
  useSensor,
  useSensors,
  DragEndEvent,
} from "@dnd-kit/core";
import {
  arrayMove,
  SortableContext,
  sortableKeyboardCoordinates,
  verticalListSortingStrategy,
} from "@dnd-kit/sortable";
import { PageLayout } from "@/components/layout/page-layout";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  useWorkQueue,
  useNextIssue,
  useBulkRerank,
  useAutoRankIssues,
  useRemoveIssueRank,
} from "@/hooks/use-work-queue";
import { SortableIssueCard } from "@/components/work-queue/sortable-issue-card";
import { Sparkles, ListOrdered, AlertCircle, ArrowRight, Loader2 } from "lucide-react";

export default function WorkQueuePage() {
  const router = useRouter();
  const [filter, setFilter] = useState<string | undefined>();

  const { data: workQueue = [], isLoading } = useWorkQueue({
    status: filter,
    limit: 100
  });
  const { data: nextIssue } = useNextIssue();
  const bulkRerankMutation = useBulkRerank();
  const autoRankMutation = useAutoRankIssues();
  const removeRankMutation = useRemoveIssueRank();

  const [localQueue, setLocalQueue] = useState(workQueue);

  // Update local queue when server data changes
  useEffect(() => {
    setLocalQueue(workQueue);
  }, [workQueue]);

  const sensors = useSensors(
    useSensor(PointerSensor),
    useSensor(KeyboardSensor, {
      coordinateGetter: sortableKeyboardCoordinates,
    })
  );

  const handleDragEnd = (event: DragEndEvent) => {
    const { active, over } = event;

    if (over && active.id !== over.id) {
      const oldIndex = localQueue.findIndex((issue) => issue.id === active.id);
      const newIndex = localQueue.findIndex((issue) => issue.id === over.id);

      const newQueue = arrayMove(localQueue, oldIndex, newIndex);
      setLocalQueue(newQueue);

      // Update ranks on server
      const issueRanks = newQueue.map((issue, index) => ({
        issue_id: issue.id,
        rank: index + 1,
      }));

      bulkRerankMutation.mutate(issueRanks);
    }
  };

  const handleAutoRank = () => {
    autoRankMutation.mutate();
  };

  const handleRemoveFromQueue = (issueId: string) => {
    removeRankMutation.mutate(issueId);
  };

  const openIssues = localQueue.filter((i) => i.status === "open");
  const inProgressIssues = localQueue.filter((i) => i.status === "in_progress");
  const allIssues = localQueue;

  const renderIssueList = (issues: typeof workQueue) => {
    if (issues.length === 0) {
      return (
        <div className="flex h-64 items-center justify-center">
          <div className="text-center">
            <ListOrdered className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
            <p className="text-lg font-medium">No issues in queue</p>
            <p className="text-sm text-muted-foreground mt-2">
              Click "Auto-Rank" to automatically prioritize your issues
            </p>
          </div>
        </div>
      );
    }

    return (
      <DndContext sensors={sensors} collisionDetection={closestCenter} onDragEnd={handleDragEnd}>
        <SortableContext items={issues.map((i) => i.id)} strategy={verticalListSortingStrategy}>
          <div className="space-y-2">
            {issues.map((issue) => (
              <SortableIssueCard
                key={issue.id}
                issue={issue}
                onRemove={() => handleRemoveFromQueue(issue.id)}
                onView={() => router.push(`/issues/${issue.id}`)}
              />
            ))}
          </div>
        </SortableContext>
      </DndContext>
    );
  };

  return (
    <PageLayout
      title="Work Queue"
      description="Prioritized list of issues to work on"
      isLoading={isLoading}
    >
      <div className="flex-1 page-padding space-y-6">
        {/* Next Issue Card */}
        {nextIssue && (
          <Card className="border-2 border-primary">
            <CardHeader className="pb-3">
              <div className="flex items-start justify-between">
                <div>
                  <CardTitle className="flex items-center gap-2">
                    <ArrowRight className="h-5 w-5 text-primary" />
                    Next Issue to Work On
                  </CardTitle>
                  <CardDescription className="mt-1">
                    Rank #{nextIssue.work_rank} • {nextIssue.type}
                  </CardDescription>
                </div>
                <div className="flex gap-2">
                  <Badge
                    variant={
                      nextIssue.priority === "critical" || nextIssue.priority === "high"
                        ? "destructive"
                        : "secondary"
                    }
                  >
                    {nextIssue.priority}
                  </Badge>
                  <Badge variant="outline">{nextIssue.status}</Badge>
                </div>
              </div>
            </CardHeader>
            <CardContent>
              <h3 className="font-semibold text-lg mb-2">{nextIssue.title}</h3>
              <p className="text-sm text-muted-foreground line-clamp-2 mb-4">
                {nextIssue.description}
              </p>
              <Button onClick={() => router.push(`/issues/${nextIssue.id}`)}>
                Start Working
                <ArrowRight className="ml-2 h-4 w-4" />
              </Button>
            </CardContent>
          </Card>
        )}

        {/* Controls */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <AlertCircle className="h-5 w-5 text-muted-foreground" />
            <span className="text-sm text-muted-foreground">
              {localQueue.length} issues in queue • Drag to reorder
            </span>
          </div>
          <Button
            onClick={handleAutoRank}
            disabled={autoRankMutation.isPending}
            variant="outline"
          >
            {autoRankMutation.isPending ? (
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
            ) : (
              <Sparkles className="mr-2 h-4 w-4" />
            )}
            Auto-Rank Issues
          </Button>
        </div>

        {/* Tabbed Issue Lists */}
        <Tabs defaultValue="all" className="w-full">
          <TabsList>
            <TabsTrigger value="all" onClick={() => setFilter(undefined)}>
              All ({allIssues.length})
            </TabsTrigger>
            <TabsTrigger value="open" onClick={() => setFilter("open")}>
              Open ({openIssues.length})
            </TabsTrigger>
            <TabsTrigger value="in_progress" onClick={() => setFilter("in_progress")}>
              In Progress ({inProgressIssues.length})
            </TabsTrigger>
          </TabsList>

          <TabsContent value="all" className="mt-6">
            {renderIssueList(allIssues)}
          </TabsContent>

          <TabsContent value="open" className="mt-6">
            {renderIssueList(openIssues)}
          </TabsContent>

          <TabsContent value="in_progress" className="mt-6">
            {renderIssueList(inProgressIssues)}
          </TabsContent>
        </Tabs>
      </div>
    </PageLayout>
  );
}
