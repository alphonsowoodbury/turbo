"use client";

import { PageLayout } from "@/components/layout/page-layout";
import { StaffList } from "@/components/staff/staff-list";

export default function StaffPage() {
  return (
    <PageLayout title="Staff">
      <div className="flex-1 page-padding">
        <StaffList />
      </div>
    </PageLayout>
  );
}
