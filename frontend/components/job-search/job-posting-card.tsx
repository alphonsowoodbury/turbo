"use client";

import { useRouter } from "next/navigation";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Building2, MapPin, DollarSign, Calendar, ExternalLink, ThumbsUp, ThumbsDown, Briefcase } from "lucide-react";
import { MatchScoreGauge } from "./match-score-gauge";

export interface JobPosting {
  id: string;
  source: string;
  source_url: string;
  company_name: string;
  job_title: string;
  job_description?: string;
  location?: string;
  remote_policy?: string;
  salary_min?: number;
  salary_max?: number;
  status: string;
  match_score?: number;
  match_reasons?: {
    title_match?: string;
    matched_keywords?: string[];
    remote_match?: boolean;
    salary_meets_minimum?: boolean;
    [key: string]: any;
  };
  posted_date?: string;
  discovered_date: string;
}

interface JobPostingCardProps {
  job: JobPosting;
  onStatusChange?: (jobId: string, status: string) => void;
}

export function JobPostingCard({ job, onStatusChange }: JobPostingCardProps) {
  const router = useRouter();

  const formatSalary = (min?: number, max?: number) => {
    if (!min && !max) return null;
    const formatNum = (n: number) => `$${(n / 1000).toFixed(0)}k`;
    if (min && max) return `${formatNum(min)} - ${formatNum(max)}`;
    if (min) return `${formatNum(min)}+`;
    return null;
  };

  const formatDate = (dateStr?: string) => {
    if (!dateStr) return "Unknown";
    const date = new Date(dateStr);
    const now = new Date();
    const diffDays = Math.floor((now.getTime() - date.getTime()) / (1000 * 60 * 60 * 24));

    if (diffDays === 0) return "Today";
    if (diffDays === 1) return "Yesterday";
    if (diffDays < 7) return `${diffDays} days ago`;
    return date.toLocaleDateString("en-US", { month: "short", day: "numeric" });
  };

  const getStatusColor = (status: string) => {
    const colors: Record<string, string> = {
      new: "bg-blue-500",
      interested: "bg-purple-500",
      not_interested: "bg-gray-500",
      applied: "bg-green-500",
      expired: "bg-red-500",
    };
    return colors[status] || "bg-gray-500";
  };

  const getRemoteBadgeColor = (policy?: string) => {
    if (!policy) return "bg-gray-100 text-gray-800";
    if (policy === "remote") return "bg-green-100 text-green-800";
    if (policy === "hybrid") return "bg-blue-100 text-blue-800";
    return "bg-orange-100 text-orange-800";
  };

  const salary = formatSalary(job.salary_min, job.salary_max);
  const topKeywords = job.match_reasons?.matched_keywords?.slice(0, 3) || [];

  return (
    <Card
      className="hover:shadow-lg transition-shadow cursor-pointer"
      onClick={() => router.push(`/work/job-search/postings/${job.id}`)}
    >
      <CardContent className="p-4">
        <div className="space-y-3">
          {/* Header */}
          <div className="flex items-start justify-between gap-3">
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2 mb-1">
                <h3 className="font-semibold text-lg truncate">{job.job_title}</h3>
                <Badge className={`${getStatusColor(job.status)} text-white shrink-0`}>
                  {job.status.replace(/_/g, " ")}
                </Badge>
              </div>
              <div className="flex items-center gap-2 text-sm text-muted-foreground">
                <Building2 className="h-3 w-3 shrink-0" />
                <span className="truncate">{job.company_name}</span>
              </div>
            </div>

            {/* Match Score */}
            {job.match_score !== undefined && (
              <div className="shrink-0">
                <MatchScoreGauge score={job.match_score} size="sm" showLabel={false} />
              </div>
            )}
          </div>

          {/* Details Row */}
          <div className="flex flex-wrap items-center gap-x-4 gap-y-2 text-sm text-muted-foreground">
            {job.location && (
              <div className="flex items-center gap-1">
                <MapPin className="h-3 w-3" />
                <span className="truncate max-w-[200px]">{job.location}</span>
              </div>
            )}

            {job.remote_policy && (
              <Badge variant="outline" className={getRemoteBadgeColor(job.remote_policy)}>
                {job.remote_policy}
              </Badge>
            )}

            {salary && (
              <div className="flex items-center gap-1">
                <DollarSign className="h-3 w-3" />
                <span>{salary}</span>
              </div>
            )}

            <div className="flex items-center gap-1">
              <Calendar className="h-3 w-3" />
              <span>{formatDate(job.posted_date)}</span>
            </div>
          </div>

          {/* Keywords */}
          {topKeywords.length > 0 && (
            <div className="flex flex-wrap gap-1">
              {topKeywords.map((keyword, idx) => (
                <Badge key={idx} variant="secondary" className="text-xs">
                  {keyword}
                </Badge>
              ))}
            </div>
          )}

          {/* Description Preview */}
          {job.job_description && (
            <p className="text-sm text-muted-foreground line-clamp-2">
              {job.job_description}
            </p>
          )}

          {/* Actions */}
          <div className="flex items-center justify-between pt-2 border-t">
            <div className="flex gap-2">
              <Button
                size="sm"
                variant="outline"
                onClick={(e) => {
                  e.stopPropagation();
                  onStatusChange?.(job.id, "interested");
                }}
                disabled={job.status === "interested"}
              >
                <ThumbsUp className="h-3 w-3 mr-1" />
                Interested
              </Button>
              <Button
                size="sm"
                variant="outline"
                onClick={(e) => {
                  e.stopPropagation();
                  onStatusChange?.(job.id, "not_interested");
                }}
                disabled={job.status === "not_interested"}
              >
                <ThumbsDown className="h-3 w-3 mr-1" />
                Skip
              </Button>
            </div>

            <div className="flex gap-2">
              <Button
                size="sm"
                variant="ghost"
                onClick={(e) => {
                  e.stopPropagation();
                  window.open(job.source_url, "_blank");
                }}
              >
                <ExternalLink className="h-3 w-3 mr-1" />
                View on {job.source}
              </Button>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
