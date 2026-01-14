import * as React from "react"
import Link from "next/link"
import { ChevronRight } from "lucide-react"
import { cn } from "@/lib/utils"

export interface BreadcrumbItem {
  label: string
  href?: string
}

export interface BreadcrumbProps {
  items: BreadcrumbItem[]
  className?: string
}

export function Breadcrumb({ items, className }: BreadcrumbProps) {
  return (
    <nav aria-label="Breadcrumb" className={cn("flex items-center space-x-1 text-base", className)}>
      {items.map((item, index) => {
        const isLast = index === items.length - 1

        return (
          <React.Fragment key={index}>
            {index > 0 && (
              <ChevronRight className="h-4 w-4 text-muted-foreground flex-shrink-0" />
            )}
            {item.href ? (
              <Link
                href={item.href}
                className={cn(
                  "transition-colors hover:text-foreground",
                  isLast ? "text-foreground font-semibold" : "text-muted-foreground font-semibold"
                )}
              >
                {item.label}
              </Link>
            ) : (
              <span
                className={cn(
                  isLast ? "text-foreground font-semibold" : "text-muted-foreground font-semibold"
                )}
              >
                {item.label}
              </span>
            )}
          </React.Fragment>
        )
      })}
    </nav>
  )
}
