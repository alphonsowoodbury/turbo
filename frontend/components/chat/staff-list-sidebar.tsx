"use client";

import { ScrollArea } from "@/components/ui/scroll-area";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Skeleton } from "@/components/ui/skeleton";
import { Search, MessageCircle } from "lucide-react";
import { useState } from "react";
import { cn } from "@/lib/utils";

interface Staff {
  id: string;
  handle: string;
  name: string;
  role_title?: string | null;
  role_type: string;
  is_active: boolean;
}

interface StaffListSidebarProps {
  staff: Staff[];
  selectedStaffId: string | null;
  onSelectStaff: (staffId: string) => void;
  isLoading?: boolean;
}

export function StaffListSidebar({
  staff,
  selectedStaffId,
  onSelectStaff,
  isLoading = false,
}: StaffListSidebarProps) {
  const [searchQuery, setSearchQuery] = useState("");

  // Filter staff based on search query
  const filteredStaff = staff.filter((s) => {
    const query = searchQuery.toLowerCase();
    return (
      s.name.toLowerCase().includes(query) ||
      s.handle.toLowerCase().includes(query) ||
      (s.role_title && s.role_title.toLowerCase().includes(query))
    );
  });

  // Sort staff: active first, then by name
  const sortedStaff = [...filteredStaff].sort((a, b) => {
    if (a.is_active !== b.is_active) {
      return a.is_active ? -1 : 1;
    }
    return a.name.localeCompare(b.name);
  });

  const getInitials = (name: string) => {
    const parts = name.split(" ");
    if (parts.length >= 2) {
      return `${parts[0][0]}${parts[1][0]}`.toUpperCase();
    }
    return name.slice(0, 2).toUpperCase();
  };

  const getRoleBadgeColor = (roleTitle?: string | null) => {
    if (!roleTitle) return "secondary";
    const lower = roleTitle.toLowerCase();
    if (lower.includes("board") || lower.includes("leadership")) return "default";
    if (lower.includes("advisor") || lower.includes("consultant")) return "outline";
    return "secondary";
  };

  return (
    <div className="flex flex-col h-full bg-muted/10">
      {/* Header */}
      <div className="p-4 border-b">
        <h2 className="text-lg font-semibold mb-3 flex items-center gap-2">
          <MessageCircle className="h-5 w-5" />
          Chat
        </h2>
        <div className="relative">
          <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
          <Input
            type="search"
            placeholder="Search staff..."
            className="pl-8 h-9"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />
        </div>
      </div>

      {/* Staff List */}
      <ScrollArea className="flex-1">
        <div className="p-2 space-y-1">
          {isLoading ? (
            // Loading skeletons
            Array.from({ length: 6 }).map((_, i) => (
              <div key={i} className="flex items-center gap-3 p-3 rounded-md">
                <Skeleton className="h-10 w-10 rounded-full" />
                <div className="flex-1 space-y-2">
                  <Skeleton className="h-4 w-24" />
                  <Skeleton className="h-3 w-16" />
                </div>
              </div>
            ))
          ) : sortedStaff.length === 0 ? (
            <div className="text-center py-8 text-sm text-muted-foreground">
              {searchQuery ? "No staff found" : "No staff members"}
            </div>
          ) : (
            sortedStaff.map((s) => (
              <button
                key={s.id}
                onClick={() => onSelectStaff(s.id)}
                className={cn(
                  "w-full flex items-center gap-3 p-3 rounded-md transition-colors text-left",
                  "hover:bg-accent hover:text-accent-foreground",
                  selectedStaffId === s.id && "bg-accent text-accent-foreground"
                )}
              >
                <Avatar className="h-10 w-10">
                  <AvatarFallback className={cn(
                    "text-sm font-medium",
                    !s.is_active && "opacity-50"
                  )}>
                    {getInitials(s.name)}
                  </AvatarFallback>
                </Avatar>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <p className={cn(
                      "font-medium text-sm truncate",
                      !s.is_active && "opacity-50"
                    )}>
                      {s.name}
                    </p>
                    {!s.is_active && (
                      <span className="text-xs text-muted-foreground">(Inactive)</span>
                    )}
                  </div>
                  <div className="flex items-center gap-2 mt-1">
                    <span className="text-xs text-muted-foreground truncate">
                      @{s.handle}
                    </span>
                    {s.role_title && (
                      <Badge
                        variant={getRoleBadgeColor(s.role_title)}
                        className="text-xs px-1.5 py-0 h-4"
                      >
                        {s.role_title}
                      </Badge>
                    )}
                  </div>
                </div>
              </button>
            ))
          )}
        </div>
      </ScrollArea>
    </div>
  );
}
