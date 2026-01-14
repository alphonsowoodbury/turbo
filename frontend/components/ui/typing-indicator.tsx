"use client";

import { Card, CardContent } from "@/components/ui/card";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Badge } from "@/components/ui/badge";
import { Bot } from "lucide-react";

interface TypingIndicatorProps {
  authorName?: string;
}

export function TypingIndicator({ authorName = "Claude" }: TypingIndicatorProps) {
  return (
    <Card className="shadow-none animate-in fade-in-0 slide-in-from-bottom-2 duration-300">
      <CardContent className="p-3">
        <div className="flex gap-2">
          <Avatar className="h-6 w-6 mt-0.5 flex-shrink-0">
            <AvatarFallback className="text-xs bg-purple-500/10 text-purple-500">
              <Bot className="h-3 w-3" />
            </AvatarFallback>
          </Avatar>

          <div className="flex-1 min-w-0 space-y-1">
            <div className="flex items-center gap-1.5 flex-wrap">
              <span className="text-xs font-medium">{authorName}</span>
              <Badge variant="secondary" className="text-[9px] h-3.5 px-1 bg-purple-500/10 text-purple-500">
                AI
              </Badge>
            </div>

            <div className="flex items-center gap-1">
              <div className="flex gap-1">
                <span className="w-2 h-2 bg-purple-500 rounded-full animate-bounce [animation-delay:-0.3s]"></span>
                <span className="w-2 h-2 bg-purple-500 rounded-full animate-bounce [animation-delay:-0.15s]"></span>
                <span className="w-2 h-2 bg-purple-500 rounded-full animate-bounce"></span>
              </div>
              <span className="text-xs text-muted-foreground ml-1">is thinking...</span>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
