"use client";

import { PageLayout } from "@/components/layout/page-layout";
import { useMyQueue } from "@/hooks/use-my-queue";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  CheckCircle,
  Clock,
  ListTodo,
  Target,
  Flag,
  AlertCircle,
  ExternalLink,
} from "lucide-react";
import { formatDistanceToNow } from "date-fns";
import { useRouter } from "next/navigation";

export default function MyQueuePage() {
  const { data: queue, isLoading, error } = useMyQueue(50);
  const router = useRouter();

  if (isLoading) {
    return (
      <PageLayout title="My Queue" isLoading={true}>
        <div />
      </PageLayout>
    );
  }

  if (error) {
    return (
      <PageLayout title="My Queue" error={error as Error}>
        <div />
      </PageLayout>
    );
  }

  const counts = queue?.counts || {
    action_approvals: 0,
    assigned_issues: 0,
    assigned_initiatives: 0,
    assigned_milestones: 0,
    review_requests: 0,
    total: 0,
  };

  return (
    <PageLayout title="My Queue">
      <div className="flex-1 page-padding space-y-6">
        {/* Summary Cards */}
        <div className="grid gap-4 md:grid-cols-5">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Total Items</CardTitle>
              <ListTodo className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{counts.total}</div>
              <p className="text-xs text-muted-foreground">
                All pending items
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Approvals</CardTitle>
              <CheckCircle className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{counts.action_approvals}</div>
              <p className="text-xs text-muted-foreground">
                Pending approval
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Issues</CardTitle>
              <AlertCircle className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{counts.assigned_issues}</div>
              <p className="text-xs text-muted-foreground">
                Assigned to you
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Reviews</CardTitle>
              <Clock className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{counts.review_requests}</div>
              <p className="text-xs text-muted-foreground">
                Staff requests
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Milestones</CardTitle>
              <Flag className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                {counts.assigned_initiatives + counts.assigned_milestones}
              </div>
              <p className="text-xs text-muted-foreground">
                Active goals
              </p>
            </CardContent>
          </Card>
        </div>

        {/* Tabbed Content */}
        <Tabs defaultValue="all" className="w-full">
          <TabsList>
            <TabsTrigger value="all">
              All ({counts.total})
            </TabsTrigger>
            <TabsTrigger value="approvals">
              Approvals ({counts.action_approvals})
            </TabsTrigger>
            <TabsTrigger value="issues">
              Issues ({counts.assigned_issues})
            </TabsTrigger>
            <TabsTrigger value="reviews">
              Reviews ({counts.review_requests})
            </TabsTrigger>
            <TabsTrigger value="goals">
              Goals ({counts.assigned_initiatives + counts.assigned_milestones})
            </TabsTrigger>
          </TabsList>

          <TabsContent value="all" className="space-y-4 mt-6">
            {/* Action Approvals Section */}
            {queue?.action_approvals && queue.action_approvals.length > 0 && (
              <div className="space-y-2">
                <h3 className="text-lg font-semibold flex items-center gap-2">
                  <CheckCircle className="h-5 w-5" />
                  Action Approvals
                </h3>
                <div className="grid gap-3">
                  {queue.action_approvals.map((approval) => (
                    <Card key={approval.id}>
                      <CardHeader className="pb-3">
                        <div className="flex items-start justify-between">
                          <div className="flex-1">
                            <CardTitle className="text-base">
                              {approval.action_type.replace(/_/g, " ").replace(/\b\w/g, (l) => l.toUpperCase())}
                            </CardTitle>
                            <CardDescription className="mt-1">
                              {approval.entity_type} • Requested by {approval.requested_by}
                            </CardDescription>
                          </div>
                          <Badge variant={approval.status === "pending" ? "default" : "secondary"}>
                            {approval.status}
                          </Badge>
                        </div>
                      </CardHeader>
                      <CardContent className="pb-3">
                        <div className="flex items-center justify-between">
                          <span className="text-sm text-muted-foreground">
                            {formatDistanceToNow(new Date(approval.created_at), { addSuffix: true })}
                          </span>
                          <Button size="sm" onClick={() => router.push(`/approvals`)}>
                            Review
                            <ExternalLink className="ml-2 h-3 w-3" />
                          </Button>
                        </div>
                      </CardContent>
                    </Card>
                  ))}
                </div>
              </div>
            )}

            {/* Review Requests Section */}
            {queue?.review_requests && queue.review_requests.length > 0 && (
              <div className="space-y-2">
                <h3 className="text-lg font-semibold flex items-center gap-2">
                  <Clock className="h-5 w-5" />
                  Review Requests
                </h3>
                <div className="grid gap-3">
                  {queue.review_requests.map((request) => (
                    <Card key={request.id}>
                      <CardHeader className="pb-3">
                        <div className="flex items-start justify-between">
                          <div className="flex-1">
                            <CardTitle className="text-base">{request.title}</CardTitle>
                            <CardDescription className="mt-1">{request.description}</CardDescription>
                          </div>
                          <div className="flex gap-2">
                            <Badge variant="outline">{request.request_type}</Badge>
                            <Badge variant={request.priority === "high" ? "destructive" : "secondary"}>
                              {request.priority}
                            </Badge>
                          </div>
                        </div>
                      </CardHeader>
                      <CardContent className="pb-3">
                        <div className="flex items-center justify-between">
                          <span className="text-sm text-muted-foreground">
                            {formatDistanceToNow(new Date(request.created_at), { addSuffix: true })}
                          </span>
                          <Button size="sm" onClick={() => router.push(`/staff/${request.staff_id}`)}>
                            Respond
                            <ExternalLink className="ml-2 h-3 w-3" />
                          </Button>
                        </div>
                      </CardContent>
                    </Card>
                  ))}
                </div>
              </div>
            )}

            {/* Assigned Issues Section */}
            {queue?.assigned_issues && queue.assigned_issues.length > 0 && (
              <div className="space-y-2">
                <h3 className="text-lg font-semibold flex items-center gap-2">
                  <AlertCircle className="h-5 w-5" />
                  Assigned Issues
                </h3>
                <div className="grid gap-3">
                  {queue.assigned_issues.map((issue) => (
                    <Card key={issue.id}>
                      <CardHeader className="pb-3">
                        <div className="flex items-start justify-between">
                          <div className="flex-1">
                            <CardTitle className="text-base">{issue.title}</CardTitle>
                            <CardDescription className="mt-1 line-clamp-2">
                              {issue.description}
                            </CardDescription>
                          </div>
                          <div className="flex gap-2">
                            <Badge variant="outline">{issue.type}</Badge>
                            <Badge
                              variant={
                                issue.priority === "high" || issue.priority === "critical"
                                  ? "destructive"
                                  : "secondary"
                              }
                            >
                              {issue.priority}
                            </Badge>
                          </div>
                        </div>
                      </CardHeader>
                      <CardContent className="pb-3">
                        <div className="flex items-center justify-between">
                          <div className="flex items-center gap-2">
                            <Badge variant="secondary">{issue.status}</Badge>
                            <span className="text-sm text-muted-foreground">
                              {formatDistanceToNow(new Date(issue.created_at), { addSuffix: true })}
                            </span>
                          </div>
                          <Button size="sm" onClick={() => router.push(`/issues/${issue.id}`)}>
                            View
                            <ExternalLink className="ml-2 h-3 w-3" />
                          </Button>
                        </div>
                      </CardContent>
                    </Card>
                  ))}
                </div>
              </div>
            )}

            {/* Empty State */}
            {counts.total === 0 && (
              <div className="flex h-64 items-center justify-center">
                <div className="text-center max-w-md">
                  <ListTodo className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
                  <p className="text-lg font-medium">Your queue is empty</p>
                  <p className="text-sm text-muted-foreground mt-2">
                    No pending items at the moment. Great job staying on top of things!
                  </p>
                </div>
              </div>
            )}
          </TabsContent>

          <TabsContent value="approvals" className="space-y-4 mt-6">
            {queue?.action_approvals && queue.action_approvals.length > 0 ? (
              <div className="grid gap-3">
                {queue.action_approvals.map((approval) => (
                  <Card key={approval.id}>
                    <CardHeader className="pb-3">
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <CardTitle className="text-base">
                            {approval.action_type.replace(/_/g, " ").replace(/\b\w/g, (l) => l.toUpperCase())}
                          </CardTitle>
                          <CardDescription className="mt-1">
                            {approval.entity_type} • Requested by {approval.requested_by}
                          </CardDescription>
                        </div>
                        <Badge variant={approval.status === "pending" ? "default" : "secondary"}>
                          {approval.status}
                        </Badge>
                      </div>
                    </CardHeader>
                    <CardContent className="pb-3">
                      <div className="flex items-center justify-between">
                        <span className="text-sm text-muted-foreground">
                          {formatDistanceToNow(new Date(approval.created_at), { addSuffix: true })}
                        </span>
                        <Button size="sm" onClick={() => router.push(`/approvals`)}>
                          Review
                          <ExternalLink className="ml-2 h-3 w-3" />
                        </Button>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            ) : (
              <div className="flex h-64 items-center justify-center">
                <p className="text-sm text-muted-foreground">No pending approvals</p>
              </div>
            )}
          </TabsContent>

          <TabsContent value="issues" className="space-y-4 mt-6">
            {queue?.assigned_issues && queue.assigned_issues.length > 0 ? (
              <div className="grid gap-3">
                {queue.assigned_issues.map((issue) => (
                  <Card key={issue.id}>
                    <CardHeader className="pb-3">
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <CardTitle className="text-base">{issue.title}</CardTitle>
                          <CardDescription className="mt-1 line-clamp-2">
                            {issue.description}
                          </CardDescription>
                        </div>
                        <div className="flex gap-2">
                          <Badge variant="outline">{issue.type}</Badge>
                          <Badge
                            variant={
                              issue.priority === "high" || issue.priority === "critical"
                                ? "destructive"
                                : "secondary"
                            }
                          >
                            {issue.priority}
                          </Badge>
                        </div>
                      </div>
                    </CardHeader>
                    <CardContent className="pb-3">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          <Badge variant="secondary">{issue.status}</Badge>
                          <span className="text-sm text-muted-foreground">
                            {formatDistanceToNow(new Date(issue.created_at), { addSuffix: true })}
                          </span>
                        </div>
                        <Button size="sm" onClick={() => router.push(`/issues/${issue.id}`)}>
                          View
                          <ExternalLink className="ml-2 h-3 w-3" />
                          </Button>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            ) : (
              <div className="flex h-64 items-center justify-center">
                <p className="text-sm text-muted-foreground">No assigned issues</p>
              </div>
            )}
          </TabsContent>

          <TabsContent value="reviews" className="space-y-4 mt-6">
            {queue?.review_requests && queue.review_requests.length > 0 ? (
              <div className="grid gap-3">
                {queue.review_requests.map((request) => (
                  <Card key={request.id}>
                    <CardHeader className="pb-3">
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <CardTitle className="text-base">{request.title}</CardTitle>
                          <CardDescription className="mt-1">{request.description}</CardDescription>
                        </div>
                        <div className="flex gap-2">
                          <Badge variant="outline">{request.request_type}</Badge>
                          <Badge variant={request.priority === "high" ? "destructive" : "secondary"}>
                            {request.priority}
                          </Badge>
                        </div>
                      </div>
                    </CardHeader>
                    <CardContent className="pb-3">
                      <div className="flex items-center justify-between">
                        <span className="text-sm text-muted-foreground">
                          {formatDistanceToNow(new Date(request.created_at), { addSuffix: true })}
                        </span>
                        <Button size="sm" onClick={() => router.push(`/staff/${request.staff_id}`)}>
                          Respond
                          <ExternalLink className="ml-2 h-3 w-3" />
                        </Button>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            ) : (
              <div className="flex h-64 items-center justify-center">
                <p className="text-sm text-muted-foreground">No pending reviews</p>
              </div>
            )}
          </TabsContent>

          <TabsContent value="goals" className="space-y-4 mt-6">
            {queue?.assigned_initiatives && queue.assigned_initiatives.length > 0 ? (
              <div className="space-y-4">
                <h3 className="text-lg font-semibold flex items-center gap-2">
                  <Target className="h-5 w-5" />
                  Initiatives
                </h3>
                <div className="grid gap-3">
                  {queue.assigned_initiatives.map((initiative) => (
                    <Card key={initiative.id}>
                      <CardHeader className="pb-3">
                        <div className="flex items-start justify-between">
                          <div className="flex-1">
                            <CardTitle className="text-base">{initiative.name}</CardTitle>
                            <CardDescription className="mt-1">{initiative.description}</CardDescription>
                          </div>
                          <Badge variant="secondary">{initiative.status}</Badge>
                        </div>
                      </CardHeader>
                      <CardContent className="pb-3">
                        <div className="flex items-center justify-between">
                          <span className="text-sm text-muted-foreground">
                            {formatDistanceToNow(new Date(initiative.created_at), { addSuffix: true })}
                          </span>
                          <Button size="sm" onClick={() => router.push(`/initiatives/${initiative.id}`)}>
                            View
                            <ExternalLink className="ml-2 h-3 w-3" />
                          </Button>
                        </div>
                      </CardContent>
                    </Card>
                  ))}
                </div>
              </div>
            ) : null}

            {queue?.assigned_milestones && queue.assigned_milestones.length > 0 ? (
              <div className="space-y-4">
                <h3 className="text-lg font-semibold flex items-center gap-2">
                  <Flag className="h-5 w-5" />
                  Milestones
                </h3>
                <div className="grid gap-3">
                  {queue.assigned_milestones.map((milestone) => (
                    <Card key={milestone.id}>
                      <CardHeader className="pb-3">
                        <div className="flex items-start justify-between">
                          <div className="flex-1">
                            <CardTitle className="text-base">{milestone.name}</CardTitle>
                            <CardDescription className="mt-1">{milestone.description}</CardDescription>
                          </div>
                          <Badge variant="secondary">{milestone.status}</Badge>
                        </div>
                      </CardHeader>
                      <CardContent className="pb-3">
                        <div className="flex items-center justify-between">
                          <div className="flex items-center gap-2">
                            <span className="text-sm text-muted-foreground">Due:</span>
                            <span className="text-sm font-medium">
                              {formatDistanceToNow(new Date(milestone.due_date), { addSuffix: true })}
                            </span>
                          </div>
                          <Button size="sm" onClick={() => router.push(`/milestones/${milestone.id}`)}>
                            View
                            <ExternalLink className="ml-2 h-3 w-3" />
                          </Button>
                        </div>
                      </CardContent>
                    </Card>
                  ))}
                </div>
              </div>
            ) : null}

            {(!queue?.assigned_initiatives || queue.assigned_initiatives.length === 0) &&
              (!queue?.assigned_milestones || queue.assigned_milestones.length === 0) && (
                <div className="flex h-64 items-center justify-center">
                  <p className="text-sm text-muted-foreground">No active goals</p>
                </div>
              )}
          </TabsContent>
        </Tabs>
      </div>
    </PageLayout>
  );
}
