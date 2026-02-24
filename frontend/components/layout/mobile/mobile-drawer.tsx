"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import * as DialogPrimitive from "@radix-ui/react-dialog";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import { useMobileNav } from "@/hooks/use-mobile-nav";
import { WorkspaceSwitcher } from "@/components/workspace-switcher";
import {
  LayoutDashboard,
  Calendar,
  UsersRound,
  MessageCircle,
  ListOrdered,
  StickyNote,
  Activity,
  FolderKanban,
  ListTodo,
  Flag,
  Target,
  FileText,
  FileCode2,
  GitBranch,
  BookMarked,
  Radio,
  Compass,
  Tags,
  Settings,
  X,
  ChevronDown,
} from "lucide-react";

interface NavSection {
  id: string;
  label: string;
  icon: React.ComponentType<{ className?: string }>;
  href: string;
  items?: NavItem[];
}

interface NavItem {
  href: string;
  icon: React.ComponentType<{ className?: string }>;
  label: string;
}

export function MobileDrawer() {
  const pathname = usePathname();
  const { isDrawerOpen, closeDrawer, expandedSections, toggleSection } = useMobileNav();

  const sections: NavSection[] = [
    {
      id: "projects",
      label: "Projects",
      icon: FolderKanban,
      href: "/projects",
      items: [
        { href: "/issues", icon: ListTodo, label: "Issues" },
        { href: "/milestones", icon: Flag, label: "Milestones" },
        { href: "/initiatives", icon: Target, label: "Initiatives" },
        { href: "/documents", icon: FileText, label: "Documents" },
        { href: "/blueprints", icon: FileCode2, label: "Blueprints" },
        { href: "/worktrees", icon: GitBranch, label: "Worktrees" },
      ],
    },
    {
      id: "agents",
      label: "Agents",
      icon: Activity,
      href: "/agents",
      items: [
        { href: "/agents/sessions", icon: Activity, label: "Sessions" },
      ],
    },
    {
      id: "literature",
      label: "Literature",
      icon: BookMarked,
      href: "/literature",
      items: [
        { href: "/podcasts", icon: Radio, label: "Podcasts" },
      ],
    },
  ];

  const quickLinks = [
    { href: "/", icon: LayoutDashboard, label: "Dashboard" },
    { href: "/calendar", icon: Calendar, label: "Calendar" },
    { href: "/staff", icon: UsersRound, label: "Staff" },
    { href: "/chat", icon: MessageCircle, label: "Chat" },
    { href: "/work-queue", icon: ListOrdered, label: "Work Queue" },
    { href: "/notes", icon: StickyNote, label: "Notes" },
  ];

  const bottomLinks = [
    { href: "/discoveries", icon: Compass, label: "Discovery" },
    { href: "/tags", icon: Tags, label: "Tags" },
    { href: "/settings", icon: Settings, label: "Settings" },
  ];

  const handleLinkClick = () => {
    closeDrawer();
  };

  const isActive = (href: string) => {
    if (href === "/") return pathname === "/";
    return pathname.startsWith(href);
  };

  const isSectionActive = (section: NavSection) => {
    if (isActive(section.href)) return true;
    return section.items?.some((item) => isActive(item.href)) ?? false;
  };

  return (
    <DialogPrimitive.Root open={isDrawerOpen} onOpenChange={closeDrawer}>
      <DialogPrimitive.Portal>
        <DialogPrimitive.Overlay
          className={cn(
            "fixed inset-0 z-50 bg-black/50",
            "data-[state=open]:animate-in data-[state=closed]:animate-out",
            "data-[state=closed]:fade-out-0 data-[state=open]:fade-in-0"
          )}
        />
        <DialogPrimitive.Content
          className={cn(
            "fixed left-0 top-0 z-50 h-full w-[280px] bg-background shadow-xl",
            "data-[state=open]:animate-in data-[state=closed]:animate-out",
            "data-[state=closed]:slide-out-to-left data-[state=open]:slide-in-from-left",
            "duration-300 ease-out",
            "flex flex-col safe-area-inset"
          )}
        >
          {/* Header */}
          <div className="flex h-14 items-center justify-between border-b px-4">
            <Link
              href="/"
              className="flex items-center gap-2 text-base font-semibold"
              onClick={handleLinkClick}
            >
              <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary text-primary-foreground">
                T
              </div>
              <span>Turbo</span>
            </Link>
            <DialogPrimitive.Close asChild>
              <Button variant="ghost" size="icon-mobile" className="h-10 w-10">
                <X className="h-5 w-5" />
              </Button>
            </DialogPrimitive.Close>
          </div>

          {/* Workspace Switcher */}
          <div className="p-3 border-b">
            <WorkspaceSwitcher collapsed={false} />
          </div>

          {/* Scrollable Navigation */}
          <div className="flex-1 overflow-y-auto">
            {/* Quick Links */}
            <div className="p-3 space-y-1">
              <div className="px-2 py-1 text-xs font-medium text-muted-foreground uppercase tracking-wider">
                Quick Access
              </div>
              {quickLinks.map((link) => (
                <Link key={link.href} href={link.href} onClick={handleLinkClick}>
                  <Button
                    variant={isActive(link.href) ? "secondary" : "ghost"}
                    className={cn(
                      "w-full justify-start gap-3 h-11",
                      isActive(link.href) && "bg-secondary"
                    )}
                  >
                    <link.icon className="h-5 w-5" />
                    {link.label}
                  </Button>
                </Link>
              ))}
            </div>

            <Separator />

            {/* Collapsible Sections */}
            <div className="p-3 space-y-2">
              {sections.map((section) => (
                <div key={section.id}>
                  {/* Section Header */}
                  <div
                    className={cn(
                      "flex items-center w-full rounded-md",
                      isSectionActive(section) && "bg-secondary"
                    )}
                  >
                    <Link
                      href={section.href}
                      className="flex-1"
                      onClick={handleLinkClick}
                    >
                      <Button
                        variant={isSectionActive(section) ? "secondary" : "ghost"}
                        className={cn(
                          "w-full justify-start gap-3 h-11 rounded-r-none",
                          isSectionActive(section) && "bg-secondary hover:bg-secondary"
                        )}
                      >
                        <section.icon className="h-5 w-5" />
                        <span className="flex-1 text-left">{section.label}</span>
                      </Button>
                    </Link>
                    {section.items && section.items.length > 0 && (
                      <Button
                        variant={isSectionActive(section) ? "secondary" : "ghost"}
                        size="sm"
                        className={cn(
                          "px-3 h-11 rounded-l-none border-l",
                          isSectionActive(section) && "bg-secondary hover:bg-secondary"
                        )}
                        onClick={() => toggleSection(section.id)}
                      >
                        <ChevronDown
                          className={cn(
                            "h-4 w-4 transition-transform",
                            expandedSections.includes(section.id) ? "rotate-0" : "-rotate-90"
                          )}
                        />
                      </Button>
                    )}
                  </div>

                  {/* Section Items */}
                  {section.items && expandedSections.includes(section.id) && (
                    <div className="ml-4 mt-1 space-y-1 border-l border-border pl-3">
                      {section.items.map((item) => (
                        <Link key={item.href} href={item.href} onClick={handleLinkClick}>
                          <Button
                            variant={isActive(item.href) ? "secondary" : "ghost"}
                            className={cn(
                              "w-full justify-start gap-3 h-10 text-sm",
                              isActive(item.href) && "bg-secondary"
                            )}
                          >
                            <item.icon className="h-4 w-4" />
                            {item.label}
                          </Button>
                        </Link>
                      ))}
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>

          {/* Bottom Links */}
          <div className="border-t p-3 space-y-1">
            {bottomLinks.map((link) => (
              <Link key={link.href} href={link.href} onClick={handleLinkClick}>
                <Button
                  variant={isActive(link.href) ? "secondary" : "ghost"}
                  className={cn(
                    "w-full justify-start gap-3 h-11",
                    isActive(link.href) && "bg-secondary"
                  )}
                >
                  <link.icon className="h-5 w-5" />
                  {link.label}
                </Button>
              </Link>
            ))}
          </div>
        </DialogPrimitive.Content>
      </DialogPrimitive.Portal>
    </DialogPrimitive.Root>
  );
}
