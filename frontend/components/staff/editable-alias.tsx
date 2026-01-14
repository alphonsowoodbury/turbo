"use client";

import { useState } from "react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Pencil, Check, X } from "lucide-react";
import { useUpdateStaff } from "@/hooks/use-staff";
import { useQueryClient } from "@tanstack/react-query";

interface EditableAliasProps {
  staffId: string;
  currentAlias: string | null;
  staffName: string;
  staffHandle: string;
}

export function EditableAlias({ staffId, currentAlias, staffName, staffHandle }: EditableAliasProps) {
  const [isEditing, setIsEditing] = useState(false);
  const [aliasValue, setAliasValue] = useState(currentAlias || "");
  const queryClient = useQueryClient();
  const updateStaff = useUpdateStaff();

  const handleSave = async () => {
    try {
      await updateStaff.mutateAsync({
        staffId,
        data: { alias: aliasValue.trim() || null },
      });

      // Invalidate queries to refresh data
      queryClient.invalidateQueries({ queryKey: ["staff", staffId] });
      queryClient.invalidateQueries({ queryKey: ["staff", staffId, "profile"] });

      setIsEditing(false);
    } catch (error) {
      console.error("Failed to update alias:", error);
    }
  };

  const handleCancel = () => {
    setAliasValue(currentAlias || "");
    setIsEditing(false);
  };

  if (isEditing) {
    return (
      <div className="flex items-center gap-2">
        <span className="text-sm text-muted-foreground">@</span>
        <Input
          value={aliasValue}
          onChange={(e) => setAliasValue(e.target.value)}
          placeholder="Enter alias (e.g., Maria)"
          className="h-8 w-32"
          maxLength={20}
          autoFocus
          onKeyDown={(e) => {
            if (e.key === "Enter") handleSave();
            if (e.key === "Escape") handleCancel();
          }}
        />
        <Button size="sm" variant="ghost" className="h-8 w-8 p-0" onClick={handleSave}>
          <Check className="h-4 w-4 text-green-600" />
        </Button>
        <Button size="sm" variant="ghost" className="h-8 w-8 p-0" onClick={handleCancel}>
          <X className="h-4 w-4 text-red-600" />
        </Button>
      </div>
    );
  }

  return (
    <div className="flex items-center gap-2 group">
      {currentAlias ? (
        <>
          <Badge variant="default" className="text-sm font-mono">
            @{currentAlias}
          </Badge>
          <span className="text-xs text-muted-foreground">or</span>
          <Badge variant="secondary" className="text-xs font-mono">
            @{staffHandle}
          </Badge>
        </>
      ) : (
        <>
          <Badge variant="secondary" className="text-sm font-mono">
            @{staffHandle}
          </Badge>
          <span className="text-xs text-muted-foreground italic">(set alias for shorter @ mention)</span>
        </>
      )}
      <Button
        size="sm"
        variant="ghost"
        className="h-6 w-6 p-0 opacity-0 group-hover:opacity-100 transition-opacity"
        onClick={() => setIsEditing(true)}
        title="Edit alias"
      >
        <Pencil className="h-3 w-3" />
      </Button>
    </div>
  );
}
