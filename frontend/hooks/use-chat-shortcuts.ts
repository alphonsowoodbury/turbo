import { useEffect } from "react";
import { useChatSidebar } from "./use-chat-sidebar";

export function useChatShortcuts() {
  const { toggle } = useChatSidebar();

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Cmd+M (Mac) or Ctrl+M (Windows/Linux) - Toggle chat
      if ((e.metaKey || e.ctrlKey) && e.key === "m") {
        e.preventDefault();
        toggle();
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [toggle]);
}
