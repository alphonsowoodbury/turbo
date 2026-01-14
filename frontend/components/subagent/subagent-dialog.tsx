/**
 * Subagent Dialog Component
 *
 * Allows users to select and invoke Turbo AI subagents
 */

"use client";

import { useState } from "react";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Loader2, Sparkles, ArrowLeft, CheckCircle2 } from "lucide-react";
import { useSubagents, useInvokeSubagent } from "@/hooks/use-subagent";
import { cn } from "@/lib/utils";
import { toast } from "sonner";
import { MarkdownRenderer } from "@/components/ui/markdown-renderer";

interface SubagentDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  context?: Record<string, any>;
  suggestedAgent?: string;
  suggestedPrompt?: string;
}

export function SubagentDialog({
  open,
  onOpenChange,
  context,
  suggestedAgent,
  suggestedPrompt,
}: SubagentDialogProps) {
  const [selectedAgent, setSelectedAgent] = useState<string | null>(suggestedAgent || null);
  const [prompt, setPrompt] = useState(suggestedPrompt || "");
  const [response, setResponse] = useState<string | null>(null);

  const { data: subagents, isLoading: loadingAgents } = useSubagents("turbo");
  const { mutate: invokeSubagent, isPending } = useInvokeSubagent();

  const handleInvoke = () => {
    if (!selectedAgent || !prompt.trim()) {
      toast.error("Please select an agent and enter a prompt");
      return;
    }

    invokeSubagent(
      {
        agent: selectedAgent,
        prompt: prompt.trim(),
        context,
        agent_set: "turbo",
      },
      {
        onSuccess: (data) => {
          setResponse(data.response);
          toast.success("Subagent completed successfully");
        },
        onError: (error) => {
          toast.error(error instanceof Error ? error.message : "Subagent invocation failed");
        },
      }
    );
  };

  const handleReset = () => {
    setResponse(null);
    setPrompt(suggestedPrompt || "");
  };

  const selectedAgentData = subagents?.find((a) => a.name === selectedAgent);

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-4xl max-h-[90vh] flex flex-col">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Sparkles className="h-5 w-5 text-purple-500" />
            {response ? "Subagent Response" : selectedAgent ? "Configure Request" : "Select Subagent"}
          </DialogTitle>
          <DialogDescription>
            {response
              ? "Review the subagent's analysis and recommendations"
              : selectedAgent
              ? "Customize your request to the subagent"
              : "Choose an AI assistant to help with this task"}
          </DialogDescription>
        </DialogHeader>

        <ScrollArea className="flex-1 pr-4">
          {/* Response View */}
          {response && (
            <div className="space-y-4">
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <CheckCircle2 className="h-5 w-5 text-green-500" />
                    {selectedAgentData?.description}
                  </CardTitle>
                  <CardDescription>Agent: {selectedAgent}</CardDescription>
                </CardHeader>
                <CardContent>
                  <MarkdownRenderer content={response} />
                </CardContent>
              </Card>

              <div className="flex gap-2">
                <Button onClick={handleReset} variant="outline" className="flex-1">
                  <ArrowLeft className="h-4 w-4 mr-2" />
                  Ask Another Question
                </Button>
                <Button onClick={() => onOpenChange(false)} className="flex-1">
                  Close
                </Button>
              </div>
            </div>
          )}

          {/* Prompt Configuration View */}
          {!response && selectedAgent && (
            <div className="space-y-4">
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center justify-between">
                    <span>{selectedAgentData?.description}</span>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => setSelectedAgent(null)}
                    >
                      <ArrowLeft className="h-4 w-4 mr-2" />
                      Change Agent
                    </Button>
                  </CardTitle>
                  <CardDescription>Agent: {selectedAgent}</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-2">
                    <p className="text-sm text-muted-foreground">Capabilities:</p>
                    <div className="flex flex-wrap gap-2">
                      {selectedAgentData?.capabilities.map((cap) => (
                        <Badge key={cap} variant="secondary" className="text-xs">
                          {cap}
                        </Badge>
                      ))}
                    </div>
                  </div>
                </CardContent>
              </Card>

              <div className="space-y-2">
                <label className="text-sm font-medium">Your Request</label>
                <Textarea
                  value={prompt}
                  onChange={(e) => setPrompt(e.target.value)}
                  placeholder="What would you like this agent to help you with?"
                  className="min-h-[120px]"
                />
              </div>

              <div className="flex gap-2">
                <Button
                  onClick={handleInvoke}
                  disabled={isPending || !prompt.trim()}
                  className="flex-1"
                >
                  {isPending && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                  {isPending ? "Processing..." : "Invoke Agent"}
                </Button>
              </div>
            </div>
          )}

          {/* Agent Selection View */}
          {!response && !selectedAgent && (
            <div className="space-y-3">
              {loadingAgents && (
                <div className="flex items-center justify-center py-12">
                  <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
                </div>
              )}

              {subagents?.map((agent) => (
                <Card
                  key={agent.name}
                  className={cn(
                    "cursor-pointer transition-all hover:border-primary/50",
                    selectedAgent === agent.name && "border-primary"
                  )}
                  onClick={() => setSelectedAgent(agent.name)}
                >
                  <CardHeader className="pb-3">
                    <CardTitle className="text-base flex items-center gap-2">
                      <Sparkles className="h-4 w-4 text-purple-500" />
                      {agent.description}
                    </CardTitle>
                    <CardDescription className="text-xs">
                      {agent.name}
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="flex flex-wrap gap-1.5">
                      {agent.capabilities.map((cap) => (
                        <Badge
                          key={cap}
                          variant="secondary"
                          className="text-[10px] h-5 px-2"
                        >
                          {cap}
                        </Badge>
                      ))}
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </ScrollArea>
      </DialogContent>
    </Dialog>
  );
}
