/**
 * Claude AI Settings Component
 *
 * Configure Anthropic API key and view Claude service status
 */

"use client";

import { useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import {
  Sparkles,
  CheckCircle2,
  XCircle,
  Loader2,
  AlertCircle,
  Key,
} from "lucide-react";
import { useClaudeStatus, useClaudeApiKey, useUpdateClaudeApiKey } from "@/hooks/use-settings";
import { toast } from "sonner";

export function ClaudeSettings() {
  const { data: status } = useClaudeStatus();
  const { data: apiKeyStatus } = useClaudeApiKey();
  const { mutate: updateApiKey, isPending: isUpdatingApiKey } = useUpdateClaudeApiKey();

  const [apiKey, setApiKey] = useState("");
  const [showApiKey, setShowApiKey] = useState(false);

  const handleSaveApiKey = () => {
    if (!apiKey.trim()) {
      toast.error("Please enter an API key");
      return;
    }

    if (!apiKey.startsWith("sk-ant-")) {
      toast.error("API key must start with 'sk-ant-'");
      return;
    }

    updateApiKey(apiKey, {
      onSuccess: () => {
        toast.success("API key saved successfully");
        setApiKey("");
        setShowApiKey(false);
      },
      onError: (error) => {
        toast.error(error instanceof Error ? error.message : "Failed to save API key");
      },
    });
  };


  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Sparkles className="h-5 w-5" />
          Claude AI Configuration
        </CardTitle>
        <CardDescription>
          Configure your Anthropic API key for Claude AI subagents
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* API Key Configuration */}
        <div className="space-y-4">
          <div className="flex items-center gap-2">
            <Key className="h-5 w-5" />
            <Label className="text-base">Anthropic API Key</Label>
          </div>

          {apiKeyStatus?.configured ? (
            <div className="p-4 bg-muted/30 rounded-lg space-y-3">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-green-600 flex items-center gap-2">
                    <CheckCircle2 className="h-4 w-4" />
                    API Key Configured
                  </p>
                  <p className="text-xs text-muted-foreground mt-1">
                    Source: {apiKeyStatus.source}
                  </p>
                  {apiKeyStatus.masked_key && (
                    <p className="text-xs text-muted-foreground font-mono mt-1">
                      {apiKeyStatus.masked_key}
                    </p>
                  )}
                </div>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setShowApiKey(!showApiKey)}
                >
                  {showApiKey ? "Cancel" : "Update"}
                </Button>
              </div>

              {showApiKey && (
                <div className="space-y-2 pt-3 border-t">
                  <Label htmlFor="new-api-key">New API Key</Label>
                  <div className="flex gap-2">
                    <Input
                      id="new-api-key"
                      type="password"
                      placeholder="sk-ant-api03-..."
                      value={apiKey}
                      onChange={(e) => setApiKey(e.target.value)}
                      disabled={isUpdatingApiKey}
                    />
                    <Button
                      onClick={handleSaveApiKey}
                      disabled={isUpdatingApiKey || !apiKey.trim()}
                    >
                      {isUpdatingApiKey && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                      Save
                    </Button>
                  </div>
                  <p className="text-xs text-muted-foreground">
                    Get your key from:{" "}
                    <a
                      href="https://console.anthropic.com/"
                      target="_blank"
                      rel="noopener"
                      className="underline"
                    >
                      console.anthropic.com
                    </a>
                  </p>
                </div>
              )}
            </div>
          ) : (
            <div className="space-y-3">
              <div className="p-4 bg-yellow-500/10 border border-yellow-500/20 rounded-lg">
                <div className="flex items-start gap-3">
                  <AlertCircle className="h-5 w-5 text-yellow-600 flex-shrink-0 mt-0.5" />
                  <div className="flex-1">
                    <p className="text-sm font-medium text-yellow-600">API Key Required</p>
                    <p className="text-xs text-yellow-600/80 mt-1">
                      Add your Anthropic API key to enable Claude AI features.
                    </p>
                  </div>
                </div>
              </div>

              <div className="space-y-2">
                <Label htmlFor="api-key">API Key</Label>
                <div className="flex gap-2">
                  <Input
                    id="api-key"
                    type="password"
                    placeholder="sk-ant-api03-..."
                    value={apiKey}
                    onChange={(e) => setApiKey(e.target.value)}
                    disabled={isUpdatingApiKey}
                  />
                  <Button
                    onClick={handleSaveApiKey}
                    disabled={isUpdatingApiKey || !apiKey.trim()}
                  >
                    {isUpdatingApiKey && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                    Save
                  </Button>
                </div>
                <p className="text-xs text-muted-foreground">
                  Get your key from:{" "}
                  <a
                    href="https://console.anthropic.com/"
                    target="_blank"
                    rel="noopener"
                    className="underline"
                  >
                    console.anthropic.com
                  </a>
                </p>
              </div>
            </div>
          )}
        </div>

        {/* Status Section */}
        <div className="flex items-center justify-between p-4 bg-muted/50 rounded-lg">
          <div className="flex items-center gap-3">
            <div>
              <p className="text-sm font-medium">Service Status</p>
              <p className="text-xs text-muted-foreground">
                {status?.available ? "Claude service is running" : "Claude service unavailable"}
              </p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            {status?.available ? (
              <Badge variant="outline" className="bg-green-500/10 text-green-600 border-green-500/20">
                <CheckCircle2 className="h-3 w-3 mr-1" />
                Online
              </Badge>
            ) : (
              <Badge variant="outline" className="bg-red-500/10 text-red-600 border-red-500/20">
                <XCircle className="h-3 w-3 mr-1" />
                Offline
              </Badge>
            )}
            {status?.authenticated && (
              <Badge variant="outline" className="bg-blue-500/10 text-blue-600 border-blue-500/20">
                <CheckCircle2 className="h-3 w-3 mr-1" />
                Authenticated
              </Badge>
            )}
          </div>
        </div>

        {/* Service Info */}
        {status?.available && (
          <div className="p-4 bg-muted/30 rounded-lg text-sm">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-muted-foreground">Model</p>
                <p className="font-medium font-mono text-xs">claude-sonnet-4-5-20250929</p>
              </div>
              <div>
                <p className="text-muted-foreground">Available Subagents</p>
                <p className="font-medium">{status.subagents_count || 0} agents</p>
              </div>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
