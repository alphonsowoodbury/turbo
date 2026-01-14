"use client";

import Link from "next/link";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Loader2 } from "lucide-react";
import { formatDistanceToNow } from "date-fns";
import {
  MessageSquare,
  Edit,
  CheckCircle2,
  Circle,
  AlertCircle,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { useIssues } from "@/hooks/use-issues";

interface Issue {
  id: string;
  title: string;
  status: string;
  priority: string;
  type: string;
  updated_at: string;
  created_at: string;
}

interface Comment {
  id: string;
  content: string;
  issue_id: string;
  created_at: string;
  updated_at: string;
}

interface ActivityFeedProps {
  projectId: string;
  maxItems?: number;
}

type ActivityItem = {
  id: string;
  type: "issue_created" | "issue_updated" | "comment_added";
  timestamp: string;
  issue: Issue;
  comment?: Comment;
};

export function ActivityFeed({
  projectId,
  maxItems = 10,
}: ActivityFeedProps) {
  const { data: issues, isLoading } = useIssues({ project_id: projectId });

  // TODO: Fetch comments when comments API is ready
  const comments: Comment[] = [];

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-8">
        <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
      </div>
    );
  }

  if (!issues || issues.length === 0) {
    return (
      <p className="text-sm text-muted-foreground py-4">
        No recent activity to display
      </p>
    );
  }

  // Combine issues and comments into activity items
  const activities: ActivityItem[] = [];

  // Add recently created issues
  issues.forEach((issue) => {
    const createdTime = new Date(issue.created_at).getTime();
    const updatedTime = new Date(issue.updated_at).getTime();

    // Check if issue was created recently (within 5 minutes of updated time)
    if (Math.abs(updatedTime - createdTime) < 5 * 60 * 1000) {
      activities.push({
        id: `issue-created-${issue.id}`,
        type: "issue_created",
        timestamp: issue.created_at,
        issue,
      });
    } else {
      // Otherwise it's an update
      activities.push({
        id: `issue-updated-${issue.id}`,
        type: "issue_updated",
        timestamp: issue.updated_at,
        issue,
      });
    }
  });

  // Add recent comments
  comments.forEach((comment) => {
    const issue = issues.find((i) => i.id === comment.issue_id);
    if (issue) {
      activities.push({
        id: `comment-${comment.id}`,
        type: "comment_added",
        timestamp: comment.created_at,
        issue,
        comment,
      });
    }
  });

  // Sort by timestamp descending
  const sortedActivities = activities.sort(
    (a, b) =>
      new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime()
  );

  const getActivityIcon = (type: ActivityItem["type"]) => {
    switch (type) {
      case "issue_created":
        return <Circle className="h-4 w-4 text-green-500" />;
      case "issue_updated":
        return <Edit className="h-4 w-4 text-blue-500" />;
      case "comment_added":
        return <MessageSquare className="h-4 w-4 text-purple-500" />;
    }
  };

  const getActivityText = (activity: ActivityItem) => {
    switch (activity.type) {
      case "issue_created":
        return (
          <>
            <span className="font-medium">New issue created:</span>{" "}
            <Link
              href={`/issues/${activity.issue.id}`}
              className="text-primary hover:underline"
            >
              {activity.issue.title}
            </Link>
          </>
        );
      case "issue_updated":
        return (
          <>
            <span className="font-medium">Issue updated:</span>{" "}
            <Link
              href={`/issues/${activity.issue.id}`}
              className="text-primary hover:underline"
            >
              {activity.issue.title}
            </Link>
          </>
        );
      case "comment_added":
        return (
          <>
            <span className="font-medium">Comment added to:</span>{" "}
            <Link
              href={`/issues/${activity.issue.id}`}
              className="text-primary hover:underline"
            >
              {activity.issue.title}
            </Link>
            {activity.comment && (
              <p className="text-xs text-muted-foreground mt-1 line-clamp-2">
                {activity.comment.content}
              </p>
            )}
          </>
        );
    }
  };

  if (sortedActivities.length === 0) {
    return (
      <p className="text-sm text-muted-foreground py-4">
        No recent activity to display
      </p>
    );
  }

  const displayedActivities = sortedActivities.slice(0, maxItems);
  const hasMore = sortedActivities.length > maxItems;

  return (
    <>
      <div className="space-y-4">
        {displayedActivities.map((activity) => (
          <div
            key={activity.id}
            className="flex gap-3 text-sm border-b pb-3 last:border-0 last:pb-0"
          >
            <div className="mt-0.5">{getActivityIcon(activity.type)}</div>
            <div className="flex-1 space-y-1">
              <div className="text-sm">{getActivityText(activity)}</div>
              <div className="text-xs text-muted-foreground">
                {formatDistanceToNow(new Date(activity.timestamp))} ago
              </div>
            </div>
          </div>
        ))}
      </div>
      {hasMore && (
        <div className="flex justify-center mt-4">
          <Link href={`/projects/${projectId}`}>
            <Button variant="outline" size="sm">
              View More ({sortedActivities.length} total)
            </Button>
          </Link>
        </div>
      )}
    </>
  );
}