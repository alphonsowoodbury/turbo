"use client";

import { Badge } from "@/components/ui/badge";

interface MatchScoreGaugeProps {
  score: number;
  size?: "sm" | "md" | "lg";
  showLabel?: boolean;
}

export function MatchScoreGauge({ score, size = "md", showLabel = true }: MatchScoreGaugeProps) {
  const getScoreColor = (score: number) => {
    if (score >= 90) return "bg-green-500";
    if (score >= 70) return "bg-blue-500";
    if (score >= 50) return "bg-yellow-500";
    return "bg-gray-500";
  };

  const getScoreLabel = (score: number) => {
    if (score >= 90) return "Excellent Match";
    if (score >= 70) return "Good Match";
    if (score >= 50) return "Moderate Match";
    return "Poor Match";
  };

  const sizeClasses = {
    sm: "h-2 w-24",
    md: "h-3 w-32",
    lg: "h-4 w-48",
  };

  const textSizeClasses = {
    sm: "text-xs",
    md: "text-sm",
    lg: "text-base",
  };

  return (
    <div className="flex items-center gap-2">
      {/* Progress bar */}
      <div className={`relative ${sizeClasses[size]} bg-gray-200 rounded-full overflow-hidden`}>
        <div
          className={`absolute top-0 left-0 h-full ${getScoreColor(score)} transition-all duration-300`}
          style={{ width: `${score}%` }}
        />
      </div>

      {/* Score text */}
      <span className={`font-semibold ${textSizeClasses[size]}`}>
        {Math.round(score)}%
      </span>

      {/* Label badge */}
      {showLabel && size !== "sm" && (
        <Badge variant="outline" className={`${getScoreColor(score)} text-white border-none`}>
          {getScoreLabel(score)}
        </Badge>
      )}
    </div>
  );
}
