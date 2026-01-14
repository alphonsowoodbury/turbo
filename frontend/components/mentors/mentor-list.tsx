"use client";

import { useState } from "react";
import { useMentors } from "@/hooks/use-mentors";
import { MentorCard } from "./mentor-card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Loader2 } from "lucide-react";

export function MentorList() {
  const [workspace, setWorkspace] = useState<string | undefined>(undefined);
  const [isActive, setIsActive] = useState<boolean>(true);

  const { data: mentors, isLoading, error } = useMentors({
    workspace,
    is_active: isActive,
  });

  if (isLoading) {
    return (
      <div className="flex h-64 items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex h-64 items-center justify-center">
        <div className="text-center">
          <p className="text-sm text-muted-foreground">
            Failed to load mentors
          </p>
          <p className="mt-1 text-xs text-destructive">
            {error instanceof Error ? error.message : "Unknown error"}
          </p>
        </div>
      </div>
    );
  }

  const filteredMentors = mentors || [];

  return (
    <div className="space-y-6">
      <Tabs defaultValue="all" className="w-full">
        <TabsList>
          <TabsTrigger value="all" onClick={() => setWorkspace(undefined)}>
            All
          </TabsTrigger>
          <TabsTrigger value="personal" onClick={() => setWorkspace("personal")}>
            Personal
          </TabsTrigger>
          <TabsTrigger value="freelance" onClick={() => setWorkspace("freelance")}>
            Freelance
          </TabsTrigger>
          <TabsTrigger value="work" onClick={() => setWorkspace("work")}>
            Work
          </TabsTrigger>
        </TabsList>

        <TabsContent value={workspace || "all"} className="mt-6">
          {filteredMentors.length === 0 ? (
            <div className="flex h-64 items-center justify-center">
              <div className="text-center max-w-md">
                <p className="text-sm text-muted-foreground">
                  No mentors found
                </p>
                <p className="text-xs text-muted-foreground mt-2">
                  Get started by creating your first mentor. They will have access to your workspace context and can provide personalized guidance.
                </p>
              </div>
            </div>
          ) : (
            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
              {filteredMentors.map((mentor) => (
                <MentorCard key={mentor.id} mentor={mentor} />
              ))}
            </div>
          )}
        </TabsContent>
      </Tabs>
    </div>
  );
}
