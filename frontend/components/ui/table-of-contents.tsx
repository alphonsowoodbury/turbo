"use client";

import { useEffect, useState } from "react";
import { cn } from "@/lib/utils";
import { ScrollArea } from "@/components/ui/scroll-area";

interface TOCItem {
  id: string;
  title: string;
  level: number;
}

interface TableOfContentsProps {
  content: string;
  className?: string;
}

export function TableOfContents({ content, className }: TableOfContentsProps) {
  const [tocItems, setTocItems] = useState<TOCItem[]>([]);
  const [activeId, setActiveId] = useState<string>("");

  useEffect(() => {
    // Extract headings from markdown
    const headingRegex = /^(#{1,6})\s+(.+)$/gm;
    const items: TOCItem[] = [];
    let match;

    while ((match = headingRegex.exec(content)) !== null) {
      const level = match[1].length;
      const title = match[2].trim();
      const id = title
        .toLowerCase()
        .replace(/[^\w\s-]/g, "")
        .replace(/\s+/g, "-");

      items.push({ id, title, level });
    }

    setTocItems(items);
  }, [content]);

  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            setActiveId(entry.target.id);
          }
        });
      },
      { rootMargin: "-80px 0px -80% 0px" }
    );

    const headings = document.querySelectorAll("h1, h2, h3, h4, h5, h6");
    headings.forEach((heading) => observer.observe(heading));

    return () => {
      headings.forEach((heading) => observer.unobserve(heading));
    };
  }, [tocItems]);

  const handleClick = (id: string) => {
    const element = document.getElementById(id);
    if (element) {
      element.scrollIntoView({ behavior: "smooth", block: "start" });
    }
  };

  if (tocItems.length === 0) {
    return null;
  }

  return (
    <div className={cn("space-y-2", className)}>
      <div className="px-2 py-1 text-xs font-medium text-muted-foreground uppercase">
        On this page
      </div>
      <ScrollArea className="h-[calc(100vh-200px)]">
        <nav className="space-y-1">
          {tocItems.map((item) => (
            <button
              key={item.id}
              onClick={() => handleClick(item.id)}
              className={cn(
                "block w-full text-left text-sm hover:text-foreground transition-colors py-1 px-2 rounded",
                item.level === 1 && "font-medium",
                item.level === 2 && "pl-4",
                item.level === 3 && "pl-6 text-xs",
                item.level === 4 && "pl-8 text-xs",
                item.level === 5 && "pl-10 text-xs",
                item.level === 6 && "pl-12 text-xs",
                activeId === item.id
                  ? "text-primary bg-primary/10 font-medium"
                  : "text-muted-foreground hover:bg-accent"
              )}
            >
              {item.title}
            </button>
          ))}
        </nav>
      </ScrollArea>
    </div>
  );
}