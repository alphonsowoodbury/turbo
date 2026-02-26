"use client";

import { useState } from "react";
import Link from "next/link";
import { PageLayout } from "@/components/layout/page-layout";
import { usePendingApprovals, useApproveAction, useDenyAction } from "@/hooks/use-action-approvals";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { CheckCircle, XCircle, AlertTriangle, Shield, Clock, ExternalLink } from "lucide-react";
import { cn } from "@/lib/utils";
import { formatDistanceToNow } from "date-fns";
import { toast } from "sonner";
import type { ActionApproval } from "@/lib/types";

const riskColors: Record<string, string> = {
  safe: "bg-green-500/10 text-green-500",
  low: "bg-blue-500/10 text-blue-500",
  medium: "bg-yellow-500/10 text-yellow-500",
  high: "bg-orange-500/10 text-orange-500",
  critical: "bg-red-500/10 text-red-500",
};

const riskIcons: Record<string, typeof Shield> = {
  safe: Shield,
  low: Shield,
  medium: AlertTriangle,
  high: AlertTriangle,
  critical: AlertTriangle,
};

export default function ApprovalsPage() {
  const { data, isLoading, error } = usePendingApprovals({ limit: 100 });
  const approveAction = useApproveAction();
  const denyAction = useDenyAction();
  const [processingId, setProcessingId] = useState<string | null>(null);

  const handleApprove = async (approval: ActionApproval) => {
    setProcessingId(approval.id);
    try {
      await approveAction.mutateAsync({
        id: approval.id,
        request: {
          approved_by: "User", // TODO: Get from auth context
          execute_immediately: true,
        },
      });
      toast.success("Action approved and executed");
    } catch (error: any) {
      toast.error(`Failed to approve action: ${error.message}`);
    } finally {
      setProcessingId(null);
    }
  };

  const handleDeny = async (approval: ActionApproval) => {
    setProcessingId(approval.id);
    try {
      await denyAction.mutateAsync({
        id: approval.id,
        request: {
          denied_by: "User", // TODO: Get from auth context
          denial_reason: "User denied via approval queue",
        },
      });
      toast.success("Action denied");
    } catch (error: any) {
      toast.error(`Failed to deny action: ${error.message}`);
    } finally {
      setProcessingId(null);
    }
  };

  const pendingApprovals = data?.approvals || [];

  return (
    <PageLayout
      title="Action Approval Queue"
      isLoading={isLoading}
      error={error}
    >
      <div className="page-padding">
        {/* Stats Bar */}
        <div className="mb-6 grid grid-cols-2 gap-4 sm:grid-cols-3 md:grid-cols-5">
          <Card>
            <CardContent className="pt-6">
              <div className="text-2xl font-bold">{data?.pending_count || 0}</div>
              <div className="text-xs text-muted-foreground">Pending</div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-6">
              <div className="text-2xl font-bold text-green-500">{data?.approved_count || 0}</div>
              <div className="text-xs text-muted-foreground">Approved</div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-6">
              <div className="text-2xl font-bold text-red-500">{data?.denied_count || 0}</div>
              <div className="text-xs text-muted-foreground">Denied</div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-6">
              <div className="text-2xl font-bold text-blue-500">{data?.executed_count || 0}</div>
              <div className="text-xs text-muted-foreground">Executed</div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-6">
              <div className="text-2xl font-bold">{data?.total || 0}</div>
              <div className="text-xs text-muted-foreground">Total</div>
            </CardContent>
          </Card>
        </div>

        {/* Pending Approvals List */}
        {pendingApprovals.length > 0 ? (
          <div className="space-y-4">
            {pendingApprovals.map((approval) => {
              const RiskIcon = riskIcons[approval.risk_level];
              const isProcessing = processingId === approval.id;

              return (
                <Card key={approval.id} className="hover:border-primary/50 transition-colors">
                  <CardHeader>
                    <div className="flex items-start justify-between">
                      <div className="space-y-1 flex-1">
                        <div className="flex items-center gap-2">
                          <CardTitle className="text-lg">{approval.action_description}</CardTitle>
                          <Badge variant="secondary" className={cn("text-xs", riskColors[approval.risk_level])}>
                            <RiskIcon className="h-3 w-3 mr-1" />
                            {approval.risk_level} risk
                          </Badge>
                        </div>
                        <CardDescription>
                          {approval.action_type} on {approval.entity_type}
                          {approval.entity_title && `: ${approval.entity_title}`}
                        </CardDescription>
                      </div>
                      <div className="flex gap-2">
                        <Button
                          size="sm"
                          variant="outline"
                          className="border-green-500 text-green-500 hover:bg-green-500/10"
                          onClick={() => handleApprove(approval)}
                          disabled={isProcessing}
                        >
                          <CheckCircle className="h-4 w-4 mr-1" />
                          Approve
                        </Button>
                        <Button
                          size="sm"
                          variant="outline"
                          className="border-red-500 text-red-500 hover:bg-red-500/10"
                          onClick={() => handleDeny(approval)}
                          disabled={isProcessing}
                        >
                          <XCircle className="h-4 w-4 mr-1" />
                          Deny
                        </Button>
                      </div>
                    </div>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-3">
                      {/* AI Reasoning */}
                      {approval.ai_reasoning && (
                        <div className="rounded-md bg-muted p-3">
                          <div className="text-xs font-medium text-muted-foreground mb-1">AI Reasoning:</div>
                          <div className="text-sm">{approval.ai_reasoning}</div>
                        </div>
                      )}

                      {/* Action Parameters */}
                      {approval.action_params && Object.keys(approval.action_params).length > 0 && (
                        <div className="rounded-md border p-3">
                          <div className="text-xs font-medium text-muted-foreground mb-2">Action Parameters:</div>
                          <div className="text-xs font-mono bg-muted/50 p-2 rounded">
                            {JSON.stringify(approval.action_params, null, 2)}
                          </div>
                        </div>
                      )}

                      {/* Footer */}
                      <div className="flex items-center justify-between text-xs text-muted-foreground">
                        <div className="flex items-center gap-2">
                          <Clock className="h-3 w-3" />
                          <span>
                            Created {formatDistanceToNow(new Date(approval.created_at))} ago
                          </span>
                        </div>
                        {approval.entity_id && approval.entity_type && (
                          <Link
                            href={`/${approval.entity_type}s/${approval.entity_id}`}
                            className="flex items-center gap-1 hover:text-primary transition-colors"
                          >
                            View {approval.entity_type}
                            <ExternalLink className="h-3 w-3" />
                          </Link>
                        )}
                      </div>
                    </div>
                  </CardContent>
                </Card>
              );
            })}
          </div>
        ) : (
          <div className="flex h-64 items-center justify-center">
            <div className="text-center">
              <CheckCircle className="h-12 w-12 text-green-500 mx-auto mb-4" />
              <p className="text-sm text-muted-foreground">
                No pending approvals. AI actions are being auto-executed safely!
              </p>
            </div>
          </div>
        )}
      </div>
    </PageLayout>
  );
}
