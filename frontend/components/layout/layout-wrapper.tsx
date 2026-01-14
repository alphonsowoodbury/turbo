"use client";

import { ReactNode } from "react";
import { WorkspaceLayout } from "./workspace-layout";
import { ChatSidebar } from "./chat-sidebar";
import { Sidebar } from "./sidebar";
import { useChatSidebar } from "@/hooks/use-chat-sidebar";
import { useChatShortcuts } from "@/hooks/use-chat-shortcuts";
import { useUnifiedCreateShortcut } from "@/hooks/use-unified-create";
import { UnifiedCreateModal } from "@/components/unified-create/unified-create-modal";

interface LayoutWrapperProps {
  children: ReactNode;
}

export function LayoutWrapper({ children }: LayoutWrapperProps) {
  const { isOpen: chatOpen, width: chatWidth } = useChatSidebar();

  // Enable keyboard shortcuts
  useChatShortcuts();
  useUnifiedCreateShortcut();

  return (
    <>
      <WorkspaceLayout
        sidebar={<Sidebar />}
        chatSidebar={<ChatSidebar />}
        chatOpen={chatOpen}
        chatWidth={chatWidth}
      >
        {children}
      </WorkspaceLayout>
      <UnifiedCreateModal />
    </>
  );
}
