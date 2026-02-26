"use client";

import { ReactNode } from "react";

interface ResponsiveControlsBarProps {
  primaryAction?: ReactNode;
  children?: ReactNode;
  className?: string;
}

export function ResponsiveControlsBar({
  primaryAction,
  children,
  className = "",
}: ResponsiveControlsBarProps) {
  return (
    <div className={`mb-4 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between ${className}`}>
      {primaryAction && (
        <div className="w-full sm:w-auto">{primaryAction}</div>
      )}
      {children && (
        <div className="flex flex-wrap items-center gap-2">{children}</div>
      )}
    </div>
  );
}
