"use client";

import { ReactNode } from "react";
import { Header } from "./header";
import { AlertCircle, Loader2, RotateCcw } from "lucide-react";
import { Button } from "@/components/ui/button";
import { BreadcrumbItem } from "@/components/ui/breadcrumb";

interface PageLayoutProps {
  title: string;
  children: ReactNode;
  isLoading?: boolean;
  error?: Error | null;
  onRetry?: () => void;
  breadcrumbs?: BreadcrumbItem[];
  headerChildren?: ReactNode;
  titleControl?: ReactNode; // Control placed next to title (e.g., toggle button)
}

/**
 * PageLayout Component
 *
 * Standardized page layout that prevents header compression and enables content scrolling.
 *
 * Features:
 * - Fixed-height header that never compresses
 * - Scrollable content area
 * - Built-in loading and error states
 * - Consistent structure across all pages
 *
 * Usage:
 * ```tsx
 * <PageLayout title="My Page" isLoading={isLoading} error={error}>
 *   <div className="p-6">
 *     Your content here
 *   </div>
 * </PageLayout>
 * ```
 */
export function PageLayout({
  title,
  children,
  isLoading = false,
  error = null,
  onRetry,
  breadcrumbs,
  headerChildren,
  titleControl,
}: PageLayoutProps) {
  // Loading state
  if (isLoading) {
    return (
      <div className="flex h-full flex-col">
        <div className="flex-shrink-0">
          <Header title={title} breadcrumbs={breadcrumbs} titleControl={titleControl}>
            {headerChildren}
          </Header>
        </div>
        <div className="flex flex-1 items-center justify-center">
          <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
        </div>
      </div>
    );
  }

  // Error state
  if (error) {
    return (
      <div className="flex h-full flex-col">
        <div className="flex-shrink-0">
          <Header title={title} breadcrumbs={breadcrumbs} titleControl={titleControl}>
            {headerChildren}
          </Header>
        </div>
        <div className="flex flex-1 items-center justify-center">
          <div className="text-center max-w-md space-y-3">
            <AlertCircle className="h-10 w-10 mx-auto text-destructive" />
            <p className="text-sm font-medium">Failed to load content</p>
            <p className="text-xs text-muted-foreground">
              {error instanceof Error ? error.message : "Unknown error"}
            </p>
            {onRetry && (
              <Button onClick={onRetry} variant="outline" size="sm">
                <RotateCcw className="mr-2 h-3 w-3" />
                Retry
              </Button>
            )}
          </div>
        </div>
      </div>
    );
  }

  // Normal state
  return (
    <div className="flex h-full flex-col">
      {/* Header - wrapped with flex-shrink-0 to prevent compression */}
      <div className="flex-shrink-0">
        <Header title={title} breadcrumbs={breadcrumbs} titleControl={titleControl}>
          {headerChildren}
        </Header>
      </div>

      {/* Content area - with overflow-y-auto to enable scrolling */}
      <div className="flex-1 overflow-y-auto">
        {children}
      </div>
    </div>
  );
}
