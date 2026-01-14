"use client";

import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import rehypeHighlight from "rehype-highlight";
import { cn } from "@/lib/utils";
import { Mermaid } from "./mermaid";
import { type Components } from "react-markdown";

interface MarkdownRendererProps {
  content: string;
  className?: string;
}

export function MarkdownRenderer({ content, className }: MarkdownRendererProps) {
  // Custom components for markdown rendering
  const components: Components = {
    code({ node, inline, className, children, ...props }) {
      const match = /language-(\w+)/.exec(className || "");
      const language = match ? match[1] : null;

      // Render Mermaid diagrams for code blocks with language "mermaid"
      if (!inline && language === "mermaid") {
        return <Mermaid chart={String(children).replace(/\n$/, "")} />;
      }

      // Regular code block
      return (
        <code className={className} {...props}>
          {children}
        </code>
      );
    },
    a({ node, href, children, ...props }) {
      // Check if link is external (starts with http:// or https://)
      const isExternal = href?.startsWith("http://") || href?.startsWith("https://");

      // Open external links in new tab
      if (isExternal) {
        return (
          <a href={href} target="_blank" rel="noopener noreferrer" {...props}>
            {children}
          </a>
        );
      }

      // Internal links open normally
      return (
        <a href={href} {...props}>
          {children}
        </a>
      );
    },
  };

  return (
    <div
      className={cn(
        "prose prose-sm dark:prose-invert max-w-none",
        // Headings with proper spacing
        "prose-headings:font-semibold prose-headings:tracking-tight prose-headings:mt-6 prose-headings:mb-4",
        "prose-h1:text-2xl prose-h1:mt-8 prose-h1:mb-4",
        "prose-h2:text-xl prose-h2:mt-6 prose-h2:mb-3",
        "prose-h3:text-lg prose-h3:mt-5 prose-h3:mb-2",
        "prose-h4:text-base prose-h4:mt-4 prose-h4:mb-2",
        "prose-h5:text-sm prose-h5:mt-3 prose-h5:mb-2",
        "prose-h6:text-sm prose-h6:mt-3 prose-h6:mb-2",
        // Paragraphs with spacing
        "prose-p:text-muted-foreground prose-p:leading-relaxed prose-p:my-4",
        // Links
        "prose-a:text-primary prose-a:no-underline hover:prose-a:underline prose-a:font-medium",
        // Strong and emphasis
        "prose-strong:text-foreground prose-strong:font-semibold",
        "prose-em:text-muted-foreground prose-em:italic",
        // Inline code
        "prose-code:text-foreground prose-code:bg-muted prose-code:px-1.5 prose-code:py-0.5 prose-code:rounded-md prose-code:text-sm prose-code:font-mono prose-code:before:content-[''] prose-code:after:content-['']",
        // Code blocks
        "prose-pre:bg-muted prose-pre:border prose-pre:border-border prose-pre:rounded-lg prose-pre:p-4 prose-pre:my-4 prose-pre:overflow-x-auto",
        // Blockquotes
        "prose-blockquote:border-l-4 prose-blockquote:border-l-primary prose-blockquote:bg-muted/50 prose-blockquote:py-2 prose-blockquote:px-4 prose-blockquote:my-4 prose-blockquote:italic",
        // Lists with proper spacing and bullets
        "prose-ul:my-4 prose-ul:list-disc prose-ul:list-outside prose-ul:ml-6 prose-ul:space-y-2",
        "prose-ol:my-4 prose-ol:list-decimal prose-ol:list-outside prose-ol:ml-6 prose-ol:space-y-2",
        "prose-li:text-muted-foreground prose-li:leading-relaxed prose-li:pl-2 prose-li:my-1",
        // Nested lists
        "prose-li>ul:my-2 prose-li>ul:ml-4",
        "prose-li>ol:my-2 prose-li>ol:ml-4",
        // Tables
        "prose-table:border prose-table:border-border prose-table:my-4 prose-table:w-full",
        "prose-th:bg-muted prose-th:border prose-th:border-border prose-th:px-4 prose-th:py-2 prose-th:font-semibold prose-th:text-left",
        "prose-td:border prose-td:border-border prose-td:px-4 prose-td:py-2",
        "prose-tr:border-b prose-tr:border-border",
        // Horizontal rules
        "prose-hr:my-8 prose-hr:border-border",
        // Images
        "prose-img:rounded-lg prose-img:my-4 prose-img:border prose-img:border-border",
        className
      )}
    >
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        rehypePlugins={[rehypeHighlight]}
        components={components}
      >
        {content}
      </ReactMarkdown>
    </div>
  );
}
