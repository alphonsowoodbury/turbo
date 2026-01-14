"use client";

import { useState } from "react";
import { useStaff } from "@/hooks/use-staff";
import { StaffCard } from "./staff-card";
import { CreateStaffDialog } from "./create-staff-dialog";
import { ToolsManagementModal } from "./tools-management-modal";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Button } from "@/components/ui/button";
import { Loader2, Settings } from "lucide-react";

export function StaffList() {
  const [roleType, setRoleType] = useState<"leadership" | "domain_expert" | undefined>(undefined);
  const [isActive, setIsActive] = useState<boolean>(true);
  const [toolsModalOpen, setToolsModalOpen] = useState(false);

  const { data: staff, isLoading, error } = useStaff({
    role_type: roleType,
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
            Failed to load staff
          </p>
          <p className="mt-1 text-xs text-destructive">
            {error instanceof Error ? error.message : "Unknown error"}
          </p>
        </div>
      </div>
    );
  }

  const filteredStaff = staff || [];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between mb-6">
        <div className="flex-1" />
        <div className="flex items-center gap-2">
          <CreateStaffDialog />
          <Button
            variant="outline"
            size="sm"
            onClick={() => setToolsModalOpen(true)}
            className="flex items-center gap-2"
          >
            <Settings className="h-4 w-4" />
            Manage Tools
          </Button>
        </div>
      </div>

      <Tabs defaultValue="all" className="w-full">
        <TabsList>
          <TabsTrigger value="all" onClick={() => setRoleType(undefined)}>
            All Staff
          </TabsTrigger>
          <TabsTrigger value="leadership" onClick={() => setRoleType("leadership")}>
            Leadership
          </TabsTrigger>
          <TabsTrigger value="domain_expert" onClick={() => setRoleType("domain_expert")}>
            Domain Experts
          </TabsTrigger>
        </TabsList>

        <TabsContent value={roleType || "all"} className="mt-6">
          {filteredStaff.length === 0 ? (
            <div className="flex h-64 items-center justify-center">
              <div className="text-center max-w-md">
                <p className="text-sm text-muted-foreground">
                  No staff members found
                </p>
                <p className="text-xs text-muted-foreground mt-2">
                  Staff members are AI domain experts and leadership roles that can provide guidance, review work, and coordinate across your projects.
                </p>
              </div>
            </div>
          ) : (
            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
              {filteredStaff.map((member) => (
                <StaffCard key={member.id} staff={member} />
              ))}
            </div>
          )}
        </TabsContent>
      </Tabs>

      <ToolsManagementModal open={toolsModalOpen} onOpenChange={setToolsModalOpen} />
    </div>
  );
}
