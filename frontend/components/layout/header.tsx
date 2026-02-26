"use client";

import { Breadcrumb, BreadcrumbItem } from "@/components/ui/breadcrumb";

interface HeaderProps {
  title: string;
  children?: React.ReactNode;
  breadcrumbs?: BreadcrumbItem[];
  titleControl?: React.ReactNode; // Control placed next to title (e.g., toggle button)
}

export function Header({ title, children, breadcrumbs, titleControl }: HeaderProps) {
  return (
    <div className="flex h-14 items-center justify-between border-b px-2 sm:px-4">
      <div className="flex min-w-0 items-center gap-2">
        {breadcrumbs && breadcrumbs.length > 0 && (
          <span className="hidden sm:contents">
            <Breadcrumb items={breadcrumbs} />
            <span className="text-muted-foreground">/</span>
          </span>
        )}
        <h1 className="truncate text-sm font-semibold sm:text-base">{title}</h1>
        {titleControl && (
          <div className="flex flex-shrink-0 items-center">
            {titleControl}
          </div>
        )}
      </div>

      <div className="flex flex-shrink-0 items-center gap-2 sm:gap-4">
        {children}
      </div>
    </div>
  );
}