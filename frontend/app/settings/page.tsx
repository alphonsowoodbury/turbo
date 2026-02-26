"use client";

import { PageLayout } from "@/components/layout/page-layout";
import { ClaudeSettings } from "@/components/settings/claude-settings";

export default function SettingsPage() {
  return (
    <PageLayout title="Settings">
      <div className="page-padding space-y-6">
        <ClaudeSettings />
      </div>
    </PageLayout>
  );
}
