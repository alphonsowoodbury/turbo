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
    <div className="flex h-14 items-center justify-between border-b px-4">
      <div className="flex items-center gap-2">
        {breadcrumbs && breadcrumbs.length > 0 && (
          <>
            <Breadcrumb items={breadcrumbs} />
            <span className="text-muted-foreground">/</span>
          </>
        )}
        <h1 className="text-base font-semibold">{title}</h1>
        {titleControl && (
          <div className="flex items-center">
            {titleControl}
          </div>
        )}
      </div>

      <div className="flex items-center gap-4">
        {/* Custom children */}
        {children}
      </div>
    </div>
  );
}