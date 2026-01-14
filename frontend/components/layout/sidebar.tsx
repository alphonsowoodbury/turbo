"use client";

import { useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import {
  FolderKanban,
  LayoutDashboard,
  ListTodo,
  Settings,
  FileText,
  Tags,
  FileCode2,
  Star,
  Compass,
  ChevronDown,
  Flag,
  Target,
  PanelLeftClose,
  PanelLeftOpen,
  Calendar,
  StickyNote,
  MessageCircle,
  Activity,
  UsersRound,
  ListOrdered,
  GitBranch,
} from "lucide-react";
import { useFavorites } from "@/hooks/use-favorites";
import { useIssues } from "@/hooks/use-issues";
import { useDocuments } from "@/hooks/use-documents";
import { useProjects } from "@/hooks/use-projects";
import { useNotes } from "@/hooks/use-notes";
import { useSidebar } from "@/hooks/use-sidebar";
import { useWorkspace } from "@/hooks/use-workspace";
import { WidgetContainer, type Widget } from "@/components/widgets/widget-container";
import { CalendarWidget } from "@/components/widgets/calendar-widget";
import { NotesWidget } from "@/components/widgets/notes-widget";
import { WorkspaceSwitcher } from "@/components/workspace-switcher";

const navigation = [
  { name: "Discovery", href: "/discoveries", icon: Compass },
  { name: "Tags", href: "/tags", icon: Tags },
];

const widgets: Widget[] = [
  {
    id: "calendar",
    label: "Calendar",
    icon: Calendar,
    component: CalendarWidget,
  },
  {
    id: "notes",
    label: "Quick Notes",
    icon: StickyNote,
    component: NotesWidget,
  },
];

export function Sidebar() {
  const pathname = usePathname();
  const [projectsExpanded, setProjectsExpanded] = useState(true);
  const [teamsExpanded, setTeamsExpanded] = useState(true);
  const { data: favorites = [] } = useFavorites();
  const { isCollapsed, toggle } = useSidebar();
  const { workspace, workCompany } = useWorkspace();

  // Fetch all entity types for favorites
  const { data: allIssues = [] } = useIssues({
    ...(workspace !== "all" && {
      workspace,
      ...(workspace === "work" && workCompany && { work_company: workCompany })
    })
  });
  const { data: allDocuments = [] } = useDocuments();
  const { data: allProjects = [] } = useProjects();
  const { data: allNotes = [] } = useNotes({
    ...(workspace !== "all" && {
      workspace,
      ...(workspace === "work" && workCompany && { work_company: workCompany })
    })
  });

  // Map favorites to their actual entities
  const favoriteItems = favorites
    .map((f) => {
      let item, href, icon;

      if (f.item_type === "issue") {
        item = allIssues.find((i) => i.id === f.item_id);
        href = `/issues/${f.item_id}`;
        icon = ListTodo;
      } else if (f.item_type === "document") {
        item = allDocuments.find((d) => d.id === f.item_id);
        href = `/documents?id=${f.item_id}`;
        icon = FileText;
      } else if (f.item_type === "project") {
        item = allProjects.find((p) => p.id === f.item_id);
        href = `/projects/${f.item_id}`;
        icon = FolderKanban;
      } else if (f.item_type === "note") {
        item = allNotes.find((n) => n.id === f.item_id);
        href = `/notes?id=${f.item_id}`;
        icon = StickyNote;
      } else if (f.item_type === "tag") {
        href = `/tags/${f.item_id}`;
        icon = Tags;
        item = { id: f.item_id, title: "Tag" }; // Placeholder
      } else if (f.item_type === "blueprint") {
        href = `/blueprints/${f.item_id}`;
        icon = FileCode2;
        item = { id: f.item_id, title: "Blueprint" }; // Placeholder
      }

      return item ? { ...item, href, icon, type: f.item_type } : null;
    })
    .filter(Boolean)
    .slice(0, 10);

  const isProjectsActive = pathname.startsWith("/projects") ||
                           pathname.startsWith("/issues") ||
                           pathname.startsWith("/milestones") ||
                           pathname.startsWith("/initiatives") ||
                           pathname.startsWith("/blueprints") ||
                           pathname.startsWith("/documents") ||
                           pathname.startsWith("/worktrees");

  const isTeamsActive = pathname.startsWith("/chat") ||
                        pathname.startsWith("/agents") ||
                        pathname.startsWith("/scripts");

  const shouldShowProjects = true; // Always show projects

  return (
    <div className={cn(
      "flex h-screen flex-col border-r bg-background transition-all duration-300",
      isCollapsed ? "w-16" : "w-64"
    )}>
      {/* Logo */}
      <div className="flex h-14 items-center justify-between border-b px-4">
        <Link href="/" className="flex items-center gap-2 text-base font-semibold">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary text-primary-foreground flex-shrink-0">
            T
          </div>
          {!isCollapsed && <span>Turbo</span>}
        </Link>
        {!isCollapsed && (
          <Button
            variant="ghost"
            size="icon"
            onClick={toggle}
            className="h-8 w-8"
          >
            <PanelLeftClose className="h-4 w-4" />
          </Button>
        )}
        {isCollapsed && (
          <Button
            variant="ghost"
            size="icon"
            onClick={toggle}
            className="h-8 w-8 absolute left-2"
          >
            <PanelLeftOpen className="h-4 w-4" />
          </Button>
        )}
      </div>

      <Separator className="my-0" />

      {/* Workspace Switcher */}
      <div className="p-2">
        <WorkspaceSwitcher collapsed={isCollapsed} />
      </div>

      <Separator className="my-0" />

      {/* Scrollable Navigation Area */}
      <div className="flex-1 overflow-y-auto scrollbar-hide">
        {/* Favorites */}
        {!isCollapsed && favoriteItems.length > 0 && (
          <div className="p-2 space-y-1">
            <div className="px-2 py-1 text-xs font-medium text-muted-foreground">Favorites</div>
            {favoriteItems.map((item) => {
              const ItemIcon = item.icon;
              return (
                <Link key={item.id} href={item.href}>
                  <Button
                    variant="ghost"
                    className={cn(
                      "w-full justify-start gap-2 h-7 px-2 text-xs",
                      pathname === item.href && "bg-secondary"
                    )}
                  >
                    <Star className="h-3 w-3 fill-yellow-400 text-yellow-400 flex-shrink-0" />
                    <ItemIcon className="h-3 w-3 flex-shrink-0" />
                    <span className="truncate">{item.title || item.name}</span>
                  </Button>
                </Link>
              );
            })}
          </div>
        )}

        {!isCollapsed && favoriteItems.length > 0 && <Separator className="my-0" />}

        {/* Navigation */}
        <nav className="space-y-1 p-2">
        {/* Dashboard */}
        <Link href="/">
          <Button
            variant={pathname === "/" ? "secondary" : "ghost"}
            className={cn(
              "w-full gap-3",
              isCollapsed ? "justify-center px-2" : "justify-start",
              pathname === "/" && "bg-secondary"
            )}
          >
            <LayoutDashboard className="h-4 w-4 flex-shrink-0" />
            {!isCollapsed && "Dashboard"}
          </Button>
        </Link>

        {/* Calendar */}
        <Link href="/calendar">
          <Button
            variant={pathname === "/calendar" ? "secondary" : "ghost"}
            className={cn(
              "w-full gap-3",
              isCollapsed ? "justify-center px-2" : "justify-start",
              pathname === "/calendar" && "bg-secondary"
            )}
          >
            <Calendar className="h-4 w-4 flex-shrink-0" />
            {!isCollapsed && "Calendar"}
          </Button>
        </Link>

        {/* Staff Button */}
        <Link href="/staff">
          <Button
            variant={pathname.startsWith("/staff") ? "secondary" : "ghost"}
            className={cn(
              "w-full gap-3",
              isCollapsed ? "justify-center px-2" : "justify-start",
              pathname.startsWith("/staff") && "bg-secondary"
            )}
          >
            <UsersRound className="h-4 w-4 flex-shrink-0" />
            {!isCollapsed && "Staff"}
          </Button>
        </Link>

        {/* Chat Button */}
        <Link href="/chat">
          <Button
            variant={pathname.startsWith("/chat") ? "secondary" : "ghost"}
            className={cn(
              "w-full gap-3",
              isCollapsed ? "justify-center px-2" : "justify-start",
              pathname.startsWith("/chat") && "bg-secondary"
            )}
          >
            <MessageCircle className="h-4 w-4 flex-shrink-0" />
            {!isCollapsed && "Chat"}
          </Button>
        </Link>

        {/* Work Queue */}
        <Link href="/work-queue">
          <Button
            variant={pathname === "/work-queue" ? "secondary" : "ghost"}
            className={cn(
              "w-full gap-3",
              isCollapsed ? "justify-center px-2" : "justify-start",
              pathname === "/work-queue" && "bg-secondary"
            )}
          >
            <ListOrdered className="h-4 w-4 flex-shrink-0" />
            {!isCollapsed && "Work Queue"}
          </Button>
        </Link>

        {/* Notes */}
        <Link href="/notes">
          <Button
            variant={pathname === "/notes" ? "secondary" : "ghost"}
            className={cn(
              "w-full gap-3",
              isCollapsed ? "justify-center px-2" : "justify-start",
              pathname === "/notes" && "bg-secondary"
            )}
          >
            <StickyNote className="h-4 w-4 flex-shrink-0" />
            {!isCollapsed && "Notes"}
          </Button>
        </Link>

        {/* Agents Section with Submenu */}
        {!isCollapsed ? (
          <div>
            <div
              className={cn(
                "flex items-center w-full rounded-md",
                isTeamsActive && "bg-secondary"
              )}
            >
              <Link href="/agents" className="flex-1">
                <Button
                  variant={isTeamsActive ? "secondary" : "ghost"}
                  className={cn(
                    "w-full justify-start gap-3 rounded-r-none",
                    isTeamsActive && "bg-secondary hover:bg-secondary"
                  )}
                >
                  <Activity className="h-4 w-4 flex-shrink-0" />
                  <span className="flex-1 text-left">Agents</span>
                </Button>
              </Link>
              <Button
                variant={isTeamsActive ? "secondary" : "ghost"}
                size="sm"
                className={cn(
                  "px-2 rounded-l-none border-l",
                  isTeamsActive && "bg-secondary hover:bg-secondary"
                )}
                onClick={(e) => {
                  e.stopPropagation();
                  setTeamsExpanded(!teamsExpanded);
                }}
              >
                <ChevronDown
                  className={cn(
                    "h-4 w-4 transition-transform",
                    teamsExpanded ? "rotate-0" : "-rotate-90"
                  )}
                />
              </Button>
            </div>

            {/* Agents Submenu */}
            {teamsExpanded && (
              <div className="ml-4 mt-1 space-y-1 border-l border-border pl-2">
                <Link href="/agents/sessions">
                  <Button
                    variant={pathname.startsWith("/agents/sessions") ? "secondary" : "ghost"}
                    className={cn(
                      "w-full justify-start gap-3 text-sm",
                      pathname.startsWith("/agents/sessions") && "bg-secondary"
                    )}
                  >
                    <Activity className="h-4 w-4" />
                    Sessions
                  </Button>
                </Link>
              </div>
            )}
          </div>
        ) : (
          <Link href="/agents">
            <Button
              variant={isTeamsActive ? "secondary" : "ghost"}
              className={cn(
                "w-full justify-center px-2",
                isTeamsActive && "bg-secondary"
              )}
            >
              <Activity className="h-4 w-4 flex-shrink-0" />
            </Button>
          </Link>
        )}

        {/* Projects Section with Submenu */}
        {shouldShowProjects && (
          !isCollapsed ? (
            <div>
              <div
                className={cn(
                  "flex items-center w-full rounded-md",
                  isProjectsActive && "bg-secondary"
                )}
              >
                <Link href="/projects" className="flex-1">
                  <Button
                    variant={isProjectsActive ? "secondary" : "ghost"}
                    className={cn(
                      "w-full justify-start gap-3 rounded-r-none",
                      isProjectsActive && "bg-secondary hover:bg-secondary"
                    )}
                  >
                    <FolderKanban className="h-4 w-4 flex-shrink-0" />
                    <span className="flex-1 text-left">Projects</span>
                  </Button>
                </Link>
                <Button
                  variant={isProjectsActive ? "secondary" : "ghost"}
                  size="sm"
                  className={cn(
                    "px-2 rounded-l-none border-l",
                    isProjectsActive && "bg-secondary hover:bg-secondary"
                  )}
                  onClick={(e) => {
                    e.stopPropagation();
                    setProjectsExpanded(!projectsExpanded);
                  }}
                >
                  <ChevronDown
                    className={cn(
                      "h-4 w-4 transition-transform",
                      projectsExpanded ? "rotate-0" : "-rotate-90"
                    )}
                  />
                </Button>
              </div>

              {/* Projects Submenu */}
              {projectsExpanded && (
                <div className="ml-4 mt-1 space-y-1 border-l border-border pl-2">
                  <Link href="/issues">
                    <Button
                      variant={pathname.startsWith("/issues") ? "secondary" : "ghost"}
                      className={cn(
                        "w-full justify-start gap-3 text-sm",
                        pathname.startsWith("/issues") && "bg-secondary"
                      )}
                    >
                      <ListTodo className="h-4 w-4" />
                      Issues
                    </Button>
                  </Link>

                  <Link href="/milestones">
                    <Button
                      variant={pathname.startsWith("/milestones") ? "secondary" : "ghost"}
                      className={cn(
                        "w-full justify-start gap-3 text-sm",
                        pathname.startsWith("/milestones") && "bg-secondary"
                      )}
                    >
                      <Flag className="h-4 w-4" />
                      Milestones
                    </Button>
                  </Link>

                  <Link href="/initiatives">
                    <Button
                      variant={pathname.startsWith("/initiatives") ? "secondary" : "ghost"}
                      className={cn(
                        "w-full justify-start gap-3 text-sm",
                        pathname.startsWith("/initiatives") && "bg-secondary"
                      )}
                    >
                      <Target className="h-4 w-4" />
                      Initiatives
                    </Button>
                  </Link>

                  <Link href="/documents">
                    <Button
                      variant={pathname.startsWith("/documents") ? "secondary" : "ghost"}
                      className={cn(
                        "w-full justify-start gap-3 text-sm",
                        pathname.startsWith("/documents") && "bg-secondary"
                      )}
                    >
                      <FileText className="h-4 w-4" />
                      Documents
                    </Button>
                  </Link>

                  <Link href="/blueprints">
                    <Button
                      variant={pathname.startsWith("/blueprints") ? "secondary" : "ghost"}
                      className={cn(
                        "w-full justify-start gap-3 text-sm",
                        pathname.startsWith("/blueprints") && "bg-secondary"
                      )}
                    >
                      <FileCode2 className="h-4 w-4" />
                      Blueprints
                    </Button>
                  </Link>

                  <Link href="/worktrees">
                    <Button
                      variant={pathname.startsWith("/worktrees") ? "secondary" : "ghost"}
                      className={cn(
                        "w-full justify-start gap-3 text-sm",
                        pathname.startsWith("/worktrees") && "bg-secondary"
                      )}
                    >
                      <GitBranch className="h-4 w-4" />
                      Worktrees
                    </Button>
                  </Link>
                </div>
              )}
            </div>
          ) : (
            <Link href="/projects">
              <Button
                variant={isProjectsActive ? "secondary" : "ghost"}
                className={cn(
                  "w-full justify-center px-2",
                  isProjectsActive && "bg-secondary"
                )}
              >
                <FolderKanban className="h-4 w-4 flex-shrink-0" />
              </Button>
            </Link>
          )
        )}

        {/* Other Navigation Items */}
        {navigation.map((item) => {
          const isActive = pathname === item.href;
          return (
            <Link key={item.href} href={item.href}>
              <Button
                variant={isActive ? "secondary" : "ghost"}
                className={cn(
                  "w-full gap-3",
                  isCollapsed ? "justify-center px-2" : "justify-start",
                  isActive && "bg-secondary"
                )}
              >
                <item.icon className="h-4 w-4 flex-shrink-0" />
                {!isCollapsed && item.name}
              </Button>
            </Link>
          );
        })}
        </nav>
      </div>

      {/* Widgets - Fixed at bottom */}
      {!isCollapsed && (
        <div className="flex-none p-2">
          <WidgetContainer
            widgets={widgets}
            defaultWidget="calendar"
            defaultMinimized={true}
          />
        </div>
      )}

      <Separator className="flex-none" />

      {/* Settings - Fixed at bottom */}
      <div className="flex-none p-2">
        <Link href="/settings">
          <Button
            variant="ghost"
            className={cn(
              "w-full gap-3",
              isCollapsed ? "justify-center px-2" : "justify-start"
            )}
          >
            <Settings className="h-4 w-4 flex-shrink-0" />
            {!isCollapsed && "Settings"}
          </Button>
        </Link>
      </div>
    </div>
  );
}