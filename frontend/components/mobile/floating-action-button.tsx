"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Plus, StickyNote, ListTodo, MessageCircle, X } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useUnifiedCreate } from "@/hooks/use-unified-create";
import { useIsMobile } from "@/hooks/use-mobile";
import { cn } from "@/lib/utils";
import { useRouter } from "next/navigation";

interface QuickAction {
  id: string;
  icon: React.ComponentType<{ className?: string }>;
  label: string;
  color: string;
  action: () => void;
}

/**
 * Floating Action Button with speed dial for quick capture.
 * Only renders on mobile devices.
 */
export function FloatingActionButton() {
  const [isOpen, setIsOpen] = useState(false);
  const { open } = useUnifiedCreate();
  const isMobile = useIsMobile();
  const router = useRouter();

  // Only show on mobile
  if (!isMobile) return null;

  const actions: QuickAction[] = [
    {
      id: "note",
      icon: StickyNote,
      label: "Quick Note",
      color: "bg-yellow-500 hover:bg-yellow-600",
      action: () => {
        open("note");
        setIsOpen(false);
      },
    },
    {
      id: "issue",
      icon: ListTodo,
      label: "New Issue",
      color: "bg-blue-500 hover:bg-blue-600",
      action: () => {
        open("issue");
        setIsOpen(false);
      },
    },
    {
      id: "chat",
      icon: MessageCircle,
      label: "Chat",
      color: "bg-green-500 hover:bg-green-600",
      action: () => {
        router.push("/chat");
        setIsOpen(false);
      },
    },
  ];

  return (
    <div className="fixed bottom-20 right-4 z-40 mobile-only">
      {/* Speed dial actions */}
      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ opacity: 0, scale: 0.8 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.8 }}
            className="absolute bottom-16 right-0 flex flex-col-reverse gap-3"
          >
            {actions.map((action, index) => (
              <motion.div
                key={action.id}
                initial={{ opacity: 0, y: 20, scale: 0.8 }}
                animate={{ opacity: 1, y: 0, scale: 1 }}
                exit={{ opacity: 0, y: 20, scale: 0.8 }}
                transition={{ delay: index * 0.05 }}
              >
                <Button
                  onClick={action.action}
                  className={cn(
                    "h-12 rounded-full shadow-lg flex items-center gap-2 pr-4 text-white",
                    action.color
                  )}
                >
                  <div className="h-12 w-12 flex items-center justify-center">
                    <action.icon className="h-5 w-5" />
                  </div>
                  <span className="text-sm font-medium whitespace-nowrap">
                    {action.label}
                  </span>
                </Button>
              </motion.div>
            ))}
          </motion.div>
        )}
      </AnimatePresence>

      {/* Backdrop */}
      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/20 z-[-1]"
            onClick={() => setIsOpen(false)}
          />
        )}
      </AnimatePresence>

      {/* Main FAB */}
      <motion.div
        animate={{ rotate: isOpen ? 45 : 0 }}
        transition={{ duration: 0.2 }}
      >
        <Button
          onClick={() => setIsOpen(!isOpen)}
          className={cn(
            "h-14 w-14 rounded-full shadow-xl",
            isOpen
              ? "bg-muted text-muted-foreground hover:bg-muted"
              : "bg-primary hover:bg-primary/90"
          )}
        >
          {isOpen ? (
            <X className="h-6 w-6" />
          ) : (
            <Plus className="h-6 w-6" />
          )}
        </Button>
      </motion.div>
    </div>
  );
}
