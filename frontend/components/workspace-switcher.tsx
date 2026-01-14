"use client";

import { Check, ChevronDown, Globe, Package, User } from "lucide-react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { useWorkspace, getWorkspaceLabel, type Workspace } from "@/hooks/use-workspace";

const workspaces: Array<{ value: Workspace; label: string; icon: React.ElementType; company?: string }> = [
  { value: "all", label: "All Work", icon: Globe },
  { value: "personal", label: "Personal", icon: User },
  { value: "freelance", label: "Freelance", icon: Package },
];

interface WorkspaceSwitcherProps {
  collapsed?: boolean;
}

export function WorkspaceSwitcher({ collapsed = false }: WorkspaceSwitcherProps) {
  const { workspace, workCompany, setWorkspace } = useWorkspace();

  const currentWorkspace = workspaces.find((w) => {
    if (w.value === "work") {
      return workspace === "work" && workCompany === w.company;
    }
    return w.value === workspace;
  }) || workspaces[0];

  const CurrentIcon = currentWorkspace.icon;

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button
          variant="ghost"
          className={cn(
            "w-full justify-between",
            collapsed ? "px-2" : "px-3"
          )}
        >
          <div className="flex items-center gap-2">
            <CurrentIcon className="h-4 w-4 flex-shrink-0" />
            {!collapsed && (
              <span className="truncate text-sm">{currentWorkspace.label}</span>
            )}
          </div>
          {!collapsed && <ChevronDown className="h-4 w-4 flex-shrink-0 opacity-50" />}
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="start" className="w-56">
        {workspaces.map((ws) => {
          const Icon = ws.icon;
          const isActive = ws.value === workspace &&
            (ws.value !== "work" || workCompany === ws.company);

          return (
            <DropdownMenuItem
              key={`${ws.value}-${ws.company || ""}`}
              onClick={() => setWorkspace(ws.value, ws.company)}
              className="cursor-pointer"
            >
              <Icon className="mr-2 h-4 w-4" />
              <span className="flex-1">{ws.label}</span>
              {isActive && <Check className="h-4 w-4" />}
            </DropdownMenuItem>
          );
        })}
        <DropdownMenuSeparator />
        <DropdownMenuItem disabled className="text-xs text-muted-foreground">
          Switch workspace context
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
