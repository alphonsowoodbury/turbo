"use client";

import { useState } from "react";
import { Check, Tags as TagsIcon } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { TagBadge } from "./tag-badge";
import { cn } from "@/lib/utils";
import type { TagSummary } from "@/lib/types";

interface TagFilterProps {
  availableTags: TagSummary[];
  selectedTagIds: string[];
  onTagsChange: (tagIds: string[]) => void;
  mode?: "single" | "multiple";
  showSelectedCount?: boolean;
  className?: string;
}

export function TagFilter({
  availableTags,
  selectedTagIds,
  onTagsChange,
  mode = "multiple",
  showSelectedCount = true,
  className,
}: TagFilterProps) {
  const [isOpen, setIsOpen] = useState(false);

  const selectedTags = availableTags.filter((tag) =>
    selectedTagIds.includes(tag.id)
  );

  const handleTagToggle = (tagId: string) => {
    if (mode === "single") {
      onTagsChange([tagId]);
      setIsOpen(false);
    } else {
      if (selectedTagIds.includes(tagId)) {
        onTagsChange(selectedTagIds.filter((id) => id !== tagId));
      } else {
        onTagsChange([...selectedTagIds, tagId]);
      }
    }
  };

  const handleClearAll = () => {
    onTagsChange([]);
  };

  return (
    <div className={cn("flex items-center gap-2", className)}>
      <DropdownMenu open={isOpen} onOpenChange={setIsOpen}>
        <DropdownMenuTrigger asChild>
          <Button variant="outline" size="sm" className="gap-2">
            <TagsIcon className="h-4 w-4" />
            <span>Tags</span>
            {showSelectedCount && selectedTagIds.length > 0 && (
              <span className="ml-1 rounded-full bg-primary px-2 py-0.5 text-xs text-primary-foreground">
                {selectedTagIds.length}
              </span>
            )}
          </Button>
        </DropdownMenuTrigger>
        <DropdownMenuContent align="start" className="w-64">
          <DropdownMenuLabel className="flex items-center justify-between">
            <span>Filter by tags</span>
            {selectedTagIds.length > 0 && (
              <Button
                variant="ghost"
                size="sm"
                onClick={handleClearAll}
                className="h-auto p-0 text-xs hover:bg-transparent"
              >
                Clear all
              </Button>
            )}
          </DropdownMenuLabel>
          <DropdownMenuSeparator />
          {availableTags.length === 0 ? (
            <div className="px-2 py-6 text-center text-sm text-muted-foreground">
              No tags available
            </div>
          ) : (
            <div className="max-h-80 overflow-auto">
              {availableTags.map((tag) => {
                const isSelected = selectedTagIds.includes(tag.id);
                return (
                  <DropdownMenuItem
                    key={tag.id}
                    onClick={() => handleTagToggle(tag.id)}
                    className="flex items-center gap-2 cursor-pointer"
                  >
                    <div
                      className={cn(
                        "flex h-4 w-4 items-center justify-center rounded border",
                        isSelected
                          ? "border-primary bg-primary text-primary-foreground"
                          : "border-input"
                      )}
                    >
                      {isSelected && <Check className="h-3 w-3" />}
                    </div>
                    <div
                      className="h-3 w-3 rounded-full"
                      style={{ backgroundColor: tag.color }}
                    />
                    <span className="flex-1">{tag.name}</span>
                  </DropdownMenuItem>
                );
              })}
            </div>
          )}
        </DropdownMenuContent>
      </DropdownMenu>

      {selectedTags.length > 0 && (
        <div className="flex flex-wrap items-center gap-1">
          {selectedTags.map((tag) => (
            <TagBadge
              key={tag.id}
              tag={tag}
              size="sm"
              onRemove={() => handleTagToggle(tag.id)}
            />
          ))}
        </div>
      )}
    </div>
  );
}
