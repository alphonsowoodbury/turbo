"use client";

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { MessageCircle, Briefcase, User } from "lucide-react";
import { Mentor } from "@/lib/api/mentors";
import { useRouter } from "next/navigation";

interface MentorCardProps {
  mentor: Mentor;
}

export function MentorCard({ mentor }: MentorCardProps) {
  const router = useRouter();

  const getWorkspaceIcon = () => {
    switch (mentor.workspace) {
      case "work":
        return <Briefcase className="h-4 w-4" />;
      case "freelance":
        return <User className="h-4 w-4" />;
      default:
        return <User className="h-4 w-4" />;
    }
  };

  const getWorkspaceColor = () => {
    switch (mentor.workspace) {
      case "work":
        return "bg-blue-500";
      case "freelance":
        return "bg-purple-500";
      default:
        return "bg-gray-500";
    }
  };

  return (
    <Card className="hover:shadow-lg transition-shadow cursor-pointer" onClick={() => router.push(`/mentors/${mentor.id}`)}>
      <CardHeader>
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <CardTitle className="text-xl">{mentor.name}</CardTitle>
            <CardDescription className="mt-1">{mentor.description}</CardDescription>
          </div>
          <div className={`w-2 h-2 rounded-full ${mentor.is_active ? "bg-green-500" : "bg-gray-400"}`} title={mentor.is_active ? "Active" : "Inactive"} />
        </div>
      </CardHeader>
      <CardContent>
        <div className="space-y-3">
          {/* Workspace Badge */}
          <div className="flex items-center gap-2">
            <Badge variant="outline" className="gap-1">
              {getWorkspaceIcon()}
              <span className="capitalize">{mentor.workspace}</span>
              {mentor.work_company && (
                <>
                  <span className="mx-1">•</span>
                  <span>{mentor.work_company}</span>
                </>
              )}
            </Badge>
          </div>

          {/* Message Count */}
          {mentor.message_count !== null && (
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              <MessageCircle className="h-4 w-4" />
              <span>{mentor.message_count} messages</span>
            </div>
          )}

          {/* Action Button */}
          <Button className="w-full" size="sm" onClick={(e) => {
            e.stopPropagation();
            router.push(`/mentors/${mentor.id}`);
          }}>
            <MessageCircle className="h-4 w-4 mr-2" />
            Start Chat
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}
