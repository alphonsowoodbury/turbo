"use client";

import { useState } from "react";
import { PageLayout } from "@/components/layout/page-layout";
import { ProjectList } from "@/components/projects/project-list";
import { CreateProjectDialog } from "@/components/projects/create-project-dialog";

export default function ProjectsPage() {
  const [createDialogOpen, setCreateDialogOpen] = useState(false);

  return (
    <PageLayout
      title="Projects"
      createLabel="New Project"
      onCreateClick={() => setCreateDialogOpen(true)}
    >
      <div className="flex-1 page-padding">
        <ProjectList />
      </div>

      <CreateProjectDialog
        open={createDialogOpen}
        onOpenChange={setCreateDialogOpen}
      />
    </PageLayout>
  );
}