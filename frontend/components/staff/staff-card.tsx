"use client";

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { MessageCircle, Shield, Users } from "lucide-react";
import { Staff } from "@/lib/api/staff";
import { useRouter } from "next/navigation";

interface StaffCardProps {
  staff: Staff;
}

export function StaffCard({ staff }: StaffCardProps) {
  const router = useRouter();

  const getRoleIcon = () => {
    return staff.role_type === "leadership" ? (
      <Shield className="h-4 w-4" />
    ) : (
      <Users className="h-4 w-4" />
    );
  };

  const getRoleColor = () => {
    return staff.role_type === "leadership"
      ? "bg-blue-500 dark:bg-blue-600"
      : "bg-purple-500 dark:bg-purple-600";
  };

  return (
    <Card className="hover:shadow-lg transition-shadow cursor-pointer" onClick={() => router.push(`/staff/${staff.id}`)}>
      <CardHeader>
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <div className="flex items-center gap-2">
              <CardTitle className="text-xl">{staff.name}</CardTitle>
              {staff.alias && (
                <Badge variant="secondary" className="text-xs font-mono">
                  @{staff.alias}
                </Badge>
              )}
            </div>
            <CardDescription className="mt-1">{staff.description}</CardDescription>
          </div>
          <div
            className={`w-2 h-2 rounded-full ${staff.is_active ? "bg-green-500" : "bg-gray-400"}`}
            title={staff.is_active ? "Active" : "Inactive"}
          />
        </div>
      </CardHeader>
      <CardContent>
        <div className="space-y-3">
          {/* Role Badge */}
          <div className="flex items-center gap-2">
            <Badge variant="outline" className="gap-1">
              {getRoleIcon()}
              <span className="capitalize">{staff.role_type.replace("_", " ")}</span>
            </Badge>
          </div>

          {/* Capabilities */}
          {staff.capabilities && staff.capabilities.length > 0 && (
            <div className="space-y-1">
              <p className="text-xs text-muted-foreground">Capabilities:</p>
              <div className="flex flex-wrap gap-1">
                {staff.capabilities.slice(0, 3).map((capability, idx) => (
                  <Badge key={idx} variant="secondary" className="text-xs">
                    {capability}
                  </Badge>
                ))}
                {staff.capabilities.length > 3 && (
                  <Badge variant="secondary" className="text-xs">
                    +{staff.capabilities.length - 3} more
                  </Badge>
                )}
              </div>
            </div>
          )}

          {/* Action Button */}
          <Button className="w-full" size="sm" onClick={(e) => {
            e.stopPropagation();
            router.push(`/staff/${staff.id}`);
          }}>
            <MessageCircle className="h-4 w-4 mr-2" />
            View Details
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}
