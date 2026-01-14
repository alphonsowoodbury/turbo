"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard,
  ListOrdered,
  Plus,
  MessageCircle,
  Menu,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { useMobileNav, type MobileTab } from "@/hooks/use-mobile-nav";
import { useUnifiedCreate } from "@/hooks/use-unified-create";

interface NavItem {
  id: MobileTab;
  href?: string;
  icon: React.ComponentType<{ className?: string }>;
  label: string;
  action?: () => void;
}

export function MobileBottomNav() {
  const pathname = usePathname();
  const { setActiveTab, openDrawer } = useMobileNav();
  const { open: openCreate } = useUnifiedCreate();

  const navItems: NavItem[] = [
    {
      id: "home",
      href: "/",
      icon: LayoutDashboard,
      label: "Home",
    },
    {
      id: "tasks",
      href: "/work-queue",
      icon: ListOrdered,
      label: "Tasks",
    },
    {
      id: "create",
      icon: Plus,
      label: "Create",
      action: () => openCreate("issue"),
    },
    {
      id: "chat",
      href: "/chat",
      icon: MessageCircle,
      label: "Chat",
    },
    {
      id: "more",
      icon: Menu,
      label: "More",
      action: openDrawer,
    },
  ];

  const getIsActive = (item: NavItem): boolean => {
    if (!item.href) return false;
    if (item.href === "/") return pathname === "/";
    return pathname.startsWith(item.href);
  };

  return (
    <nav className="fixed bottom-0 left-0 right-0 z-50 border-t bg-background safe-area-bottom mobile-only">
      <div className="flex items-center justify-around h-16">
        {navItems.map((item) => {
          const isActive = getIsActive(item);
          const isCreateButton = item.id === "create";

          if (item.href) {
            return (
              <Link
                key={item.id}
                href={item.href}
                className="flex-1"
                onClick={() => setActiveTab(item.id)}
              >
                <Button
                  variant="ghost"
                  className={cn(
                    "flex flex-col items-center justify-center gap-1 h-14 w-full rounded-none",
                    "hover:bg-transparent active:bg-accent/50",
                    isActive && "text-primary"
                  )}
                >
                  <item.icon
                    className={cn(
                      "h-5 w-5",
                      isActive && "text-primary"
                    )}
                  />
                  <span className="text-[10px] font-medium">{item.label}</span>
                </Button>
              </Link>
            );
          }

          // Action button (Create or More)
          return (
            <Button
              key={item.id}
              variant="ghost"
              onClick={item.action}
              className={cn(
                "flex flex-col items-center justify-center gap-1 h-14 flex-1 rounded-none",
                "hover:bg-transparent active:bg-accent/50",
                // Make Create button stand out
                isCreateButton && "relative"
              )}
            >
              {isCreateButton ? (
                <div className="flex items-center justify-center h-10 w-10 rounded-full bg-primary text-primary-foreground shadow-lg -mt-4">
                  <item.icon className="h-5 w-5" />
                </div>
              ) : (
                <>
                  <item.icon className="h-5 w-5" />
                  <span className="text-[10px] font-medium">{item.label}</span>
                </>
              )}
            </Button>
          );
        })}
      </div>
    </nav>
  );
}
