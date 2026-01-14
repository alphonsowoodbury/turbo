"use client";

import { useParams, useRouter } from "next/navigation";
import { PageLayout } from "@/components/layout/page-layout";
import { StaffChat } from "@/components/staff/staff-chat";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { ArrowLeft, Shield, Users } from "lucide-react";
import { useStaffProfile } from "@/hooks/use-staff";
import { cn } from "@/lib/utils";

const roleColors = {
  leadership: "bg-blue-500/10 text-blue-500 hover:bg-blue-500/20",
  domain_expert: "bg-purple-500/10 text-purple-500 hover:bg-purple-500/20",
};

export default function StaffChatPage() {
  const params = useParams();
  const router = useRouter();
  const staffId = params.id as string;

  const { data: profile, isLoading } = useStaffProfile(staffId);

  const staff = profile?.staff;

  const getRoleIcon = () => {
    if (!staff) return null;
    return staff.role_type === "leadership" ? (
      <Shield className="h-4 w-4" />
    ) : (
      <Users className="h-4 w-4" />
    );
  };

  return (
    <PageLayout
      title={staff?.name || "Staff Chat"}
      isLoading={isLoading}
    >
      <div className="flex flex-col h-full">
        {/* Header with back button */}
        <div className="flex-shrink-0 border-b p-4">
          <div className="flex items-center justify-between">
            <Button
              variant="ghost"
              size="sm"
              onClick={() => router.push(`/staff/${staffId}`)}
            >
              <ArrowLeft className="mr-2 h-4 w-4" />
              Back to Profile
            </Button>

            {staff && (
              <Badge
                variant="secondary"
                className={cn("text-xs capitalize", roleColors[staff.role_type])}
              >
                {getRoleIcon()}
                <span className="ml-1">{staff.role_type.replace("_", " ")}</span>
              </Badge>
            )}
          </div>
        </div>

        {/* Chat Interface */}
        <div className="flex-1 flex flex-col overflow-hidden">
          <div className="flex-1 overflow-y-auto">
            <StaffChat staffId={staffId} />
          </div>
        </div>
      </div>
    </PageLayout>
  );
}
