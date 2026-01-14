"use client";

import { useState } from "react";
import Link from "next/link";
import { PageLayout } from "@/components/layout/page-layout";
import { useConfiguredAgents } from "@/hooks/use-agents";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Bot,
  ChevronDown,
  ChevronRight,
  Sparkles,
  ArrowRight,
  Loader2,
} from "lucide-react";
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible";

export default function ConfiguredAgentsPage() {
  const { data: configuredData, isLoading: configuredLoading } = useConfiguredAgents();
  const [expandedAgents, setExpandedAgents] = useState<Set<string>>(new Set());

  const configuredAgents = configuredData?.agents || [];

  const toggleAgent = (agentName: string) => {
    const newExpanded = new Set(expandedAgents);
    if (newExpanded.has(agentName)) {
      newExpanded.delete(agentName);
    } else {
      newExpanded.add(agentName);
    }
    setExpandedAgents(newExpanded);
  };

  return (
    <PageLayout
      title="Configured Agents"
      isLoading={configuredLoading}
    >
      <div className="flex-1 p-6">
        <div className="mb-6">
          <p className="text-sm text-muted-foreground">
            AI agents configured with specific capabilities and system prompts
          </p>
        </div>

        {configuredLoading ? (
          <Card>
            <CardContent className="pt-6">
              <div className="py-12 text-center text-muted-foreground">
                <Loader2 className="mx-auto mb-4 h-12 w-12 animate-spin opacity-20" />
                <p>Loading agents...</p>
              </div>
            </CardContent>
          </Card>
        ) : configuredAgents.length === 0 ? (
          <Card>
            <CardContent className="pt-6">
              <div className="py-12 text-center text-muted-foreground">
                <Bot className="mx-auto mb-4 h-12 w-12 opacity-20" />
                <p>No configured agents found</p>
              </div>
            </CardContent>
          </Card>
        ) : (
          <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
            {configuredAgents.map((agent: any) => (
              <Card key={agent.name} className="transition-colors hover:border-primary/50">
                <Collapsible
                  open={expandedAgents.has(agent.name)}
                  onOpenChange={() => toggleAgent(agent.name)}
                >
                  <CardHeader className="pb-3">
                    <div className="flex items-start justify-between gap-4">
                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-2">
                          <Bot className="h-5 w-5 text-primary" />
                          <CardTitle className="text-base">{agent.name}</CardTitle>
                        </div>
                        <p className="text-sm text-muted-foreground">{agent.description}</p>
                      </div>
                      <CollapsibleTrigger asChild>
                        <Button variant="ghost" size="sm" className="h-8 w-8 p-0">
                          {expandedAgents.has(agent.name) ? (
                            <ChevronDown className="h-4 w-4" />
                          ) : (
                            <ChevronRight className="h-4 w-4" />
                          )}
                        </Button>
                      </CollapsibleTrigger>
                    </div>
                    <div className="flex flex-wrap gap-2 mt-3">
                      {agent.capabilities?.map((cap: string) => (
                        <Badge key={cap} variant="secondary" className="text-xs">
                          {cap}
                        </Badge>
                      ))}
                    </div>
                  </CardHeader>
                  <CollapsibleContent>
                    <CardContent className="pt-0 space-y-4">
                      <div>
                        <h4 className="text-sm font-semibold mb-2 flex items-center gap-2">
                          <Sparkles className="h-4 w-4" />
                          Instructions
                        </h4>
                        <div className="bg-muted/50 rounded-md p-3">
                          <p className="text-xs text-muted-foreground whitespace-pre-wrap">
                            {agent.systemPrompt}
                          </p>
                        </div>
                      </div>
                      <div>
                        <h4 className="text-sm font-semibold mb-2">Available Tools</h4>
                        <div className="flex flex-wrap gap-1">
                          {agent.tools?.map((tool: string) => (
                            <Badge key={tool} variant="outline" className="text-xs font-mono">
                              {tool.replace("mcp__turbo__", "")}
                            </Badge>
                          ))}
                        </div>
                      </div>
                      <Link href={`/agents/sessions?agent=${agent.name}`}>
                        <Button variant="outline" size="sm" className="w-full">
                          View Sessions
                          <ArrowRight className="ml-2 h-3 w-3" />
                        </Button>
                      </Link>
                    </CardContent>
                  </CollapsibleContent>
                </Collapsible>
              </Card>
            ))}
          </div>
        )}
      </div>
    </PageLayout>
  );
}
