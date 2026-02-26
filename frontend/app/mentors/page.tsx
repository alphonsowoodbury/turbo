"use client";

import { useState } from "react";
import { PageLayout } from "@/components/layout/page-layout";
import { MentorList } from "@/components/mentors/mentor-list";
import { Button } from "@/components/ui/button";
import { Plus } from "lucide-react";

export default function MentorsPage() {
  const [createDialogOpen, setCreateDialogOpen] = useState(false);

  return (
    <PageLayout
      title="Mentors"
      headerChildren={
        <Button onClick={() => setCreateDialogOpen(true)}>
          <Plus className="h-4 w-4 mr-2" />
          New Mentor
        </Button>
      }
    >
      <div className="flex-1 page-padding">
        <MentorList />
      </div>

      {/* TODO: Add CreateMentorDialog component */}
    </PageLayout>
  );
}
