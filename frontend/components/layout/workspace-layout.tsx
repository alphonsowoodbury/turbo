"use client";

import { ReactNode } from "react";
import { cn } from "@/lib/utils";
import { useSidebar } from "@/hooks/use-sidebar";
import { useIsMobile } from "@/hooks/use-mobile";
import { MobileBottomNav, MobileDrawer } from "@/components/layout/mobile";

interface WorkspaceLayoutProps {
  header?: ReactNode;
  sidebar: ReactNode;
  children: ReactNode;
  chatSidebar?: ReactNode;
  chatOpen?: boolean;
  chatWidth?: number;
}

export function WorkspaceLayout({
  header,
  sidebar,
  children,
  chatSidebar,
  chatOpen = false,
  chatWidth = 400,
}: WorkspaceLayoutProps) {
  const { isCollapsed } = useSidebar();
  const isMobile = useIsMobile();

  // Mobile Layout
  if (isMobile) {
    return (
      <div className="mobile-layout h-[100dvh] w-screen flex flex-col overflow-hidden">
        {/* Main Content Area - with bottom padding for nav */}
        <div className="flex-1 overflow-y-auto pb-16">
          {children}
        </div>

        {/* Mobile Bottom Navigation */}
        <MobileBottomNav />

        {/* Mobile Drawer (rendered as portal) */}
        <MobileDrawer />
      </div>
    );
  }

  // Desktop Layout (unchanged)
  return (
    <div
      className={cn(
        "workspace-layout h-screen w-screen overflow-hidden",
        "grid transition-all duration-200 ease-out"
      )}
      style={{
        gridTemplateColumns: `${isCollapsed ? "64px" : "256px"} 1fr ${chatOpen ? `${chatWidth}px` : "0px"}`,
        gridTemplateRows: header ? "56px 1fr" : "1fr",
        gridTemplateAreas: header
          ? `
            "header header header"
            "sidebar workspace chat"
          `
          : `
            "sidebar workspace chat"
          `,
      }}
      data-sidebar-collapsed={isCollapsed}
      data-chat-open={chatOpen}
    >
      {/* Header */}
      {header && (
        <div
          className="border-b bg-background"
          style={{ gridArea: "header" }}
        >
          {header}
        </div>
      )}

      {/* Sidebar */}
      <div
        className="border-r bg-background"
        style={{ gridArea: "sidebar" }}
      >
        {sidebar}
      </div>

      {/* Workspace */}
      <div
        className="bg-background overflow-y-auto"
        style={{ gridArea: "workspace" }}
      >
        {children}
      </div>

      {/* Chat Sidebar */}
      {chatSidebar && (
        <div
          className={cn(
            "bg-background overflow-hidden transition-all duration-200 ease-out",
            !chatOpen && "hidden"
          )}
          style={{ gridArea: "chat" }}
        >
          {chatSidebar}
        </div>
      )}
    </div>
  );
}
