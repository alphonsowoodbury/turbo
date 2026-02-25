"use client";

import { useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { PageLayout } from "@/components/layout/page-layout";
import { EditableAlias } from "@/components/staff/editable-alias";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Separator } from "@/components/ui/separator";
import {
  Shield,
  Users,
  Star,
  TrendingUp,
  MessageCircle,
  Clock,
  CheckCircle,
  Activity as ActivityIcon,
  Briefcase,
} from "lucide-react";
import { useStaffProfile } from "@/hooks/use-staff";
import { formatDistanceToNow } from "date-fns";
import { cn } from "@/lib/utils";

const roleColors: Record<string, string> = {
  leadership: "bg-blue-500/10 text-blue-500 hover:bg-blue-500/20",
  domain_expert: "bg-purple-500/10 text-purple-500 hover:bg-purple-500/20",
};

export default function StaffDetailPage() {
  const params = useParams();
  const router = useRouter();
  const staffId = params.id as string;
  const [activeTab, setActiveTab] = useState("profile");

  const { data: profile, isLoading, error } = useStaffProfile(staffId);

  const getRoleIcon = () => {
    if (!profile) return null;
    return profile.staff.role_type === "leadership" ? (
      <Shield className="h-4 w-4" />
    ) : (
      <Users className="h-4 w-4" />
    );
  };

  const renderStars = (rating: number | null) => {
    if (!rating) return <span className="text-sm text-muted-foreground">Not rated</span>;
    return (
      <div className="flex items-center gap-1">
        {[...Array(5)].map((_, i) => (
          <Star
            key={i}
            className={cn(
              "h-5 w-5",
              i < Math.floor(rating)
                ? "fill-yellow-400 text-yellow-400"
                : "text-muted-foreground"
            )}
          />
        ))}
        <span className="ml-2 text-sm font-medium">{rating.toFixed(1)}</span>
      </div>
    );
  };

  if (!profile) {
    return (
      <PageLayout
        title="Staff Not Found"
        isLoading={isLoading}
        error={error || new Error("Staff member not found")}
      >
        <div />
      </PageLayout>
    );
  }

  const staff = profile.staff;

  return (
    <PageLayout
      title={staff.name}
      isLoading={isLoading}
      error={error}
    >
      <div className="space-y-6 pb-6">
        {/* Header Card */}
        <Card>
          <CardHeader>
            <div className="flex items-start justify-between">
              <div className="space-y-2 flex-1">
                <div className="flex items-center gap-3">
                  <CardTitle className="text-2xl">{staff.name}</CardTitle>
                  <EditableAlias
                    staffId={staffId}
                    currentAlias={staff.alias}
                    staffName={staff.name}
                    staffHandle={staff.handle}
                  />
                  <Badge
                    variant="secondary"
                    className={cn("text-xs capitalize", roleColors[staff.role_type])}
                  >
                    {getRoleIcon()}
                    <span className="ml-1">{staff.role_type.replace("_", " ")}</span>
                  </Badge>
                  <div
                    className={`w-2 h-2 rounded-full ${
                      staff.is_active ? "bg-green-500" : "bg-gray-400"
                    }`}
                    title={staff.is_active ? "Active" : "Inactive"}
                  />
                </div>
                <CardDescription>{staff.description}</CardDescription>
              </div>
              <div className="flex flex-col items-end gap-2">
                {renderStars(staff.overall_rating)}
                <Button
                  size="sm"
                  onClick={() => router.push(`/staff/${staffId}/chat`)}
                >
                  <MessageCircle className="h-4 w-4 mr-2" />
                  Chat
                </Button>
              </div>
            </div>
          </CardHeader>
        </Card>

        {/* Tabs */}
        <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
          <TabsList className="grid w-full grid-cols-3">
            <TabsTrigger value="profile">
              <Users className="h-4 w-4 mr-2" />
              Profile
            </TabsTrigger>
            <TabsTrigger value="work">
              <Briefcase className="h-4 w-4 mr-2" />
              Work
            </TabsTrigger>
            <TabsTrigger value="activity">
              <ActivityIcon className="h-4 w-4 mr-2" />
              Activity
            </TabsTrigger>
          </TabsList>

          {/* Profile Tab */}
          <TabsContent value="profile" className="space-y-6 mt-6">
            {/* Performance Metrics */}
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
              <Card>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium">Completed Tasks</CardTitle>
                  <CheckCircle className="h-4 w-4 text-muted-foreground" />
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">
                    {staff.performance_metrics.completed_tasks}
                  </div>
                  <p className="text-xs text-muted-foreground">
                    {staff.performance_metrics.completion_rate.toFixed(1)}% completion rate
                  </p>
                </CardContent>
              </Card>

              <Card>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium">Avg Response Time</CardTitle>
                  <Clock className="h-4 w-4 text-muted-foreground" />
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">
                    {profile.computed_metrics.avg_completion_time_hours.toFixed(1)}h
                  </div>
                  <p className="text-xs text-muted-foreground">
                    Average completion time
                  </p>
                </CardContent>
              </Card>

              <Card>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium">Quality Score</CardTitle>
                  <TrendingUp className="h-4 w-4 text-muted-foreground" />
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">
                    {staff.performance_metrics.quality_score.toFixed(1)}%
                  </div>
                  <p className="text-xs text-muted-foreground">
                    Overall quality rating
                  </p>
                </CardContent>
              </Card>

              <Card>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium">Conversations</CardTitle>
                  <MessageCircle className="h-4 w-4 text-muted-foreground" />
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">
                    {profile.computed_metrics.total_messages}
                  </div>
                  <p className="text-xs text-muted-foreground">
                    {profile.computed_metrics.active_conversations} active
                  </p>
                </CardContent>
              </Card>
            </div>

            {/* Capabilities & Persona */}
            <div className="grid gap-6 md:grid-cols-2">
              <Card>
                <CardHeader>
                  <CardTitle className="text-base">Capabilities</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="flex flex-wrap gap-2">
                    {staff.capabilities && staff.capabilities.length > 0 ? (
                      staff.capabilities.map((capability, idx) => (
                        <Badge key={idx} variant="secondary">
                          {capability}
                        </Badge>
                      ))
                    ) : (
                      <p className="text-sm text-muted-foreground">No capabilities defined</p>
                    )}
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle className="text-base">Monitoring Scope</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3 text-sm">
                    <div>
                      <span className="font-medium">Focus: </span>
                      <span className="text-muted-foreground">{staff.monitoring_scope.focus}</span>
                    </div>
                    <div>
                      <span className="font-medium">Entity Types: </span>
                      <div className="flex flex-wrap gap-1 mt-1">
                        {staff.monitoring_scope.entity_types.map((type, idx) => (
                          <Badge key={idx} variant="outline" className="text-xs">
                            {type}
                          </Badge>
                        ))}
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>

            {/* Persona */}
            <Card>
              <CardHeader>
                <CardTitle className="text-base">Communication Style</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-sm text-muted-foreground whitespace-pre-wrap leading-relaxed">
                  {staff.persona}
                </p>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Work Tab */}
          <TabsContent value="work" className="space-y-6 mt-6">
            {/* Work Summary */}
            <div className="grid gap-4 md:grid-cols-3">
              <Card>
                <CardHeader>
                  <CardTitle className="text-sm font-medium">Review Requests</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">
                    {profile.assigned_review_requests.length}
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle className="text-sm font-medium">Assigned Issues</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">
                    {profile.assigned_issues_count}
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle className="text-sm font-medium">Pending Approvals</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">
                    {profile.pending_approvals_count}
                  </div>
                </CardContent>
              </Card>
            </div>

            {/* Review Requests */}
            {profile.assigned_review_requests.length > 0 && (
              <Card>
                <CardHeader>
                  <CardTitle className="text-base">Assigned Review Requests</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    {profile.assigned_review_requests.map((request) => (
                      <div
                        key={request.id}
                        className="flex items-start justify-between p-3 rounded-lg border bg-background hover:bg-muted/50 transition-colors"
                      >
                        <div className="space-y-1 flex-1">
                          <p className="font-medium">{request.title}</p>
                          <p className="text-xs text-muted-foreground">
                            {formatDistanceToNow(new Date(request.created_at))} ago
                          </p>
                        </div>
                        <div className="flex gap-2">
                          <Badge variant="outline" className="text-xs">
                            {request.status}
                          </Badge>
                          <Badge
                            variant="outline"
                            className={cn(
                              "text-xs",
                              request.priority === "high" && "border-red-500 text-red-500",
                              request.priority === "medium" && "border-yellow-500 text-yellow-500"
                            )}
                          >
                            {request.priority}
                          </Badge>
                        </div>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            )}
          </TabsContent>

          {/* Activity Tab */}
          <TabsContent value="activity" className="space-y-6 mt-6">
            <Card>
              <CardHeader>
                <CardTitle className="text-base">Recent Activity</CardTitle>
                <CardDescription>Latest actions and updates</CardDescription>
              </CardHeader>
              <CardContent>
                {profile.recent_activity.length > 0 ? (
                  <div className="space-y-4">
                    {profile.recent_activity.map((activity) => (
                      <div key={activity.id} className="flex gap-4">
                        <div className="flex-shrink-0 mt-1">
                          {activity.activity_type.includes("message") ? (
                            <MessageCircle className="h-4 w-4 text-muted-foreground" />
                          ) : (
                            <ActivityIcon className="h-4 w-4 text-muted-foreground" />
                          )}
                        </div>
                        <div className="flex-1 space-y-1">
                          <p className="text-sm font-medium">{activity.title}</p>
                          {activity.description && (
                            <p className="text-sm text-muted-foreground">{activity.description}</p>
                          )}
                          <p className="text-xs text-muted-foreground">
                            {formatDistanceToNow(new Date(activity.created_at))} ago
                          </p>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-sm text-muted-foreground text-center py-8">
                    No recent activity
                  </p>
                )}
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </div>
    </PageLayout>
  );
}
