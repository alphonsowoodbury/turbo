"use client";

import { useState, useEffect } from "react";
import { ChevronDown, ChevronUp, LucideIcon } from "lucide-react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";

const STORAGE_KEY = "turbo-widget-minimized";

export interface Widget {
  id: string;
  label: string;
  icon: LucideIcon;
  component: React.ComponentType;
}

interface WidgetContainerProps {
  widgets: Widget[];
  defaultWidget?: string;
  defaultMinimized?: boolean;
}

export function WidgetContainer({
  widgets,
  defaultWidget,
  defaultMinimized = true,
}: WidgetContainerProps) {
  const [isMinimized, setIsMinimized] = useState(() => {
    if (typeof window !== "undefined") {
      const saved = localStorage.getItem(STORAGE_KEY);
      return saved !== null ? JSON.parse(saved) : defaultMinimized;
    }
    return defaultMinimized;
  });

  // Persist minimized state to localStorage
  useEffect(() => {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(isMinimized));
  }, [isMinimized]);
  const [activeWidgetId, setActiveWidgetId] = useState(
    defaultWidget || widgets[0]?.id
  );

  const activeWidget = widgets.find((w) => w.id === activeWidgetId);
  const ActiveComponent = activeWidget?.component;

  if (widgets.length === 0) {
    return null;
  }

  return (
    <div className="border rounded-lg bg-card shadow-sm overflow-hidden">
      {/* Header with Minimize Toggle */}
      <div className="flex items-center justify-between px-3 py-2 border-b bg-muted/30">
        <div className="flex items-center gap-2">
          {activeWidget && (
            <>
              <activeWidget.icon className="h-4 w-4 text-muted-foreground" />
              <span className="text-sm font-medium">
                {isMinimized ? "Widgets" : activeWidget.label}
              </span>
            </>
          )}
        </div>
        <Button
          variant="ghost"
          size="icon"
          className="h-6 w-6"
          onClick={() => setIsMinimized(!isMinimized)}
        >
          {isMinimized ? (
            <ChevronDown className="h-4 w-4" />
          ) : (
            <ChevronUp className="h-4 w-4" />
          )}
        </Button>
      </div>

      {/* Expanded Content */}
      {!isMinimized && (
        <>
          {/* Tab Bar (only show if multiple widgets) */}
          {widgets.length > 1 && (
            <div className="flex border-b bg-background">
              {widgets.map((widget) => {
                const isActive = widget.id === activeWidgetId;
                const Icon = widget.icon;
                return (
                  <button
                    key={widget.id}
                    onClick={() => setActiveWidgetId(widget.id)}
                    className={cn(
                      "flex-1 flex items-center justify-center gap-2 px-3 py-2 text-sm transition-colors",
                      "hover:bg-accent/50",
                      isActive
                        ? "bg-accent text-accent-foreground font-medium border-b-2 border-primary"
                        : "text-muted-foreground"
                    )}
                  >
                    <Icon className="h-4 w-4" />
                    <span className="hidden sm:inline">{widget.label}</span>
                  </button>
                );
              })}
            </div>
          )}

          {/* Widget Content */}
          <div className="p-3">
            {ActiveComponent && <ActiveComponent />}
          </div>
        </>
      )}
    </div>
  );
}
