"use client";

import { useEffect, useRef, useState } from "react";
import mermaid from "mermaid";

interface MermaidProps {
  chart: string;
  className?: string;
}

// Initialize mermaid with default config
if (typeof window !== "undefined") {
  mermaid.initialize({
    startOnLoad: true,
    theme: "default",
    securityLevel: "loose",
    fontFamily: "ui-sans-serif, system-ui, sans-serif",
    themeVariables: {
      primaryColor: "#3b82f6",
      primaryTextColor: "#fff",
      primaryBorderColor: "#2563eb",
      lineColor: "#94a3b8",
      secondaryColor: "#8b5cf6",
      tertiaryColor: "#f59e0b",
    },
  });
}

export function Mermaid({ chart, className = "" }: MermaidProps) {
  const ref = useRef<HTMLDivElement>(null);
  const [svg, setSvg] = useState<string>("");
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const renderChart = async () => {
      if (!chart || !ref.current) return;

      try {
        // Generate a unique ID for this diagram
        const id = `mermaid-${Math.random().toString(36).substr(2, 9)}`;

        // Render the diagram
        const { svg } = await mermaid.render(id, chart);
        setSvg(svg);
        setError(null);
      } catch (err) {
        console.error("Mermaid rendering error:", err);
        setError(err instanceof Error ? err.message : "Failed to render diagram");
      }
    };

    renderChart();
  }, [chart]);

  if (error) {
    return (
      <div className={`border border-red-500 bg-red-50 dark:bg-red-950 p-4 rounded-lg ${className}`}>
        <p className="text-red-600 dark:text-red-400 font-semibold">Diagram Rendering Error:</p>
        <pre className="text-sm text-red-500 dark:text-red-300 mt-2 overflow-x-auto">
          {error}
        </pre>
      </div>
    );
  }

  return (
    <div
      ref={ref}
      className={`mermaid-diagram my-6 flex justify-center ${className}`}
      dangerouslySetInnerHTML={{ __html: svg }}
    />
  );
}