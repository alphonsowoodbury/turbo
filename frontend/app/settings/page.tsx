"use client";

import { PageLayout } from "@/components/layout/page-layout";
import { ClaudeSettings } from "@/components/settings/claude-settings";

export default function SettingsPage() {
  return (
    <PageLayout title="Settings">
      <div className="p-6 space-y-6">
        <ClaudeSettings />
      </div>
    </PageLayout>
  );
}
