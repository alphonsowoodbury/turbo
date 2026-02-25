"use client";

import { useState } from "react";
import { useParams } from "next/navigation";
import { PageLayout } from "@/components/layout/page-layout";
import { MentorChat } from "@/components/mentors/mentor-chat";
import { EditMentorDialog } from "@/components/mentors/edit-mentor-dialog";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { CollapsibleInfoPanel } from "@/components/shared/collapsible-info-panel";
import { Briefcase, User, ChevronDown } from "lucide-react";
import { useMentor } from "@/hooks/use-mentors";
import { formatDistanceToNow } from "date-fns";
import { cn } from "@/lib/utils";

const workspaceColors: Record<string, string> = {
  personal: "bg-blue-500/10 text-blue-500 hover:bg-blue-500/20",
  freelance: "bg-purple-500/10 text-purple-500 hover:bg-purple-500/20",
  work: "bg-green-500/10 text-green-500 hover:bg-green-500/20",
};

export default function MentorDetailPage() {
  const params = useParams();
  const mentorId = params.id as string;
  const [isInfoOpen, setIsInfoOpen] = useState(false);

  const { data: mentor, isLoading, error } = useMentor(mentorId);

  const getWorkspaceIcon = () => {
    if (!mentor) return null;
    switch (mentor.workspace) {
      case "work":
        return <Briefcase className="h-4 w-4" />;
      case "freelance":
        return <User className="h-4 w-4" />;
      default:
        return <User className="h-4 w-4" />;
    }
  };

  // Early return if no mentor data
  if (!mentor) {
    return (
      <PageLayout
        title="Mentor Not Found"
        isLoading={isLoading}
        error={error || new Error("Mentor not found")}
      >
        <div />
      </PageLayout>
    );
  }

  // Toggle button for collapsible info panel
  const toggleButton = (
    <Button
      variant="ghost"
      size="sm"
      onClick={() => setIsInfoOpen(!isInfoOpen)}
      className="h-8 w-8 p-0"
      aria-label={isInfoOpen ? "Hide details" : "Show details"}
    >
      <ChevronDown
        className={cn(
          "h-4 w-4 transition-transform duration-250",
          isInfoOpen && "rotate-180"
        )}
      />
    </Button>
  );

  return (
    <PageLayout
      title={mentor.name}
      isLoading={isLoading}
      error={error}
      titleControl={toggleButton}
    >
      <div className="flex flex-col h-full overflow-hidden">
        {/* Collapsible Info Panel - slides down from header */}
        <CollapsibleInfoPanel
          isOpen={isInfoOpen}
          onToggle={setIsInfoOpen}
          storageKey={`mentor-info-panel-${mentorId}`}
        >
          <div className="p-6 bg-muted/30">
            <div className="flex items-start justify-between mb-4">
              <div className="space-y-2 flex-1">
                <h2 className="text-lg font-semibold">{mentor.name}</h2>
                <p className="text-sm text-muted-foreground leading-relaxed">
                  {mentor.description}
                </p>
              </div>
              <div className="flex gap-2 ml-4">
                <EditMentorDialog mentor={mentor} />
                <Badge
                  variant="secondary"
                  className={cn("text-xs capitalize", workspaceColors[mentor.workspace])}
                >
                  {getWorkspaceIcon()}
                  <span className="ml-1">{mentor.workspace}</span>
                </Badge>
                <div
                  className={`w-2 h-2 rounded-full self-center ${
                    mentor.is_active ? "bg-green-500" : "bg-gray-400"
                  }`}
                  title={mentor.is_active ? "Active" : "Inactive"}
                />
              </div>
            </div>

            {/* Metadata */}
            <div className="grid gap-4 text-sm md:grid-cols-3 mb-6">
              <div>
                <span className="text-muted-foreground">Created: </span>
                <span>{formatDistanceToNow(new Date(mentor.created_at))} ago</span>
              </div>
              <div>
                <span className="text-muted-foreground">Updated: </span>
                <span>{formatDistanceToNow(new Date(mentor.updated_at))} ago</span>
              </div>
              {mentor.message_count !== null && (
                <div>
                  <span className="text-muted-foreground">Messages: </span>
                  <span>{mentor.message_count}</span>
                </div>
              )}
            </div>

            {/* Tabs for Persona and Context */}
            <Tabs defaultValue="persona" className="w-full">
              <TabsList className="grid w-full grid-cols-2">
                <TabsTrigger value="persona">Persona</TabsTrigger>
                <TabsTrigger value="context">Context</TabsTrigger>
              </TabsList>

              <TabsContent value="persona" className="space-y-4 mt-4">
                <div className="rounded-lg border bg-background p-4">
                  <h3 className="font-semibold mb-3 text-sm">How this mentor approaches conversations</h3>
                  <p className="text-sm text-muted-foreground whitespace-pre-wrap leading-relaxed">
                    {mentor.persona}
                  </p>
                </div>
              </TabsContent>

              <TabsContent value="context" className="space-y-4 mt-4">
                <div className="rounded-lg border bg-background p-4">
                  <h3 className="font-semibold mb-3 text-sm">Workspace Context Preferences</h3>
                  <div className="space-y-3">
                    {mentor.work_company && (
                      <div>
                        <span className="text-sm font-medium">Company: </span>
                        <span className="text-sm text-muted-foreground">{mentor.work_company}</span>
                      </div>
                    )}
                    <div className="space-y-2">
                      <p className="text-sm font-medium">Included in Context:</p>
                      <ul className="text-sm text-muted-foreground space-y-1 ml-4 list-disc">
                        {mentor.context_preferences?.include_projects && <li>Projects</li>}
                        {mentor.context_preferences?.include_issues && <li>Issues</li>}
                        {mentor.context_preferences?.include_documents && <li>Documents</li>}
                        {mentor.context_preferences?.include_influencers && <li>Influencers</li>}
                      </ul>
                      <div className="mt-2">
                        <span className="text-sm font-medium">Max Items: </span>
                        <span className="text-sm text-muted-foreground">
                          {mentor.context_preferences?.max_items || 10}
                        </span>
                      </div>
                    </div>
                  </div>
                </div>
              </TabsContent>
            </Tabs>
          </div>
        </CollapsibleInfoPanel>

        {/* Main Content - Chat Messages */}
        <div className="flex-1 overflow-y-auto p-6">
          <MentorChat mentorId={mentorId} messagesOnly={true} />
        </div>

        {/* Fixed Chat Input at Bottom */}
        <div className="flex-shrink-0 border-t bg-background p-4">
          <MentorChat mentorId={mentorId} inputOnly={true} />
        </div>
      </div>
    </PageLayout>
  );
}
