"use client";

import { useState, useRef, useEffect, forwardRef } from "react";
import { Textarea } from "@/components/ui/textarea";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { useStaff } from "@/hooks/use-staff";
import { Staff } from "@/lib/api/staff";
import { cn } from "@/lib/utils";
import { Shield, Users } from "lucide-react";

interface MentionTextareaProps
  extends React.TextareaHTMLAttributes<HTMLTextAreaElement> {
  onMentionSelect?: (staff: Staff) => void;
}

export const MentionTextarea = forwardRef<
  HTMLTextAreaElement,
  MentionTextareaProps
>(({ value, onChange, onMentionSelect, className, ...props }, ref) => {
  const [showMentions, setShowMentions] = useState(false);
  const [mentionQuery, setMentionQuery] = useState("");
  const [mentionPosition, setMentionPosition] = useState({ top: 0, left: 0 });
  const [selectedIndex, setSelectedIndex] = useState(0);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const mentionsRef = useRef<HTMLDivElement>(null);

  // Fetch all active staff for mentions
  const { data: staffList = [] } = useStaff({ is_active: true });

  // Filter staff based on mention query
  const filteredStaff = staffList.filter((staff) => {
    if (!mentionQuery) return true;
    const query = mentionQuery.toLowerCase();
    return (
      staff.name.toLowerCase().includes(query) ||
      staff.handle.toLowerCase().includes(query) ||
      (staff.alias && staff.alias.toLowerCase().includes(query))
    );
  });

  // Detect @ mentions and update dropdown
  const handleTextChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    if (onChange) onChange(e);

    const textarea = textareaRef.current;
    if (!textarea) return;

    const cursorPosition = textarea.selectionStart;
    const textBeforeCursor = textarea.value.substring(0, cursorPosition);

    // Find the last @ before cursor
    const lastAtIndex = textBeforeCursor.lastIndexOf("@");

    if (lastAtIndex !== -1) {
      // Check if there's whitespace or start of string before @
      const charBeforeAt = textBeforeCursor[lastAtIndex - 1];
      const isValidMention =
        lastAtIndex === 0 || charBeforeAt === " " || charBeforeAt === "\n";

      if (isValidMention) {
        const textAfterAt = textBeforeCursor.substring(lastAtIndex + 1);
        // Only show if no whitespace after @ and cursor is right after the query
        if (!textAfterAt.includes(" ") && !textAfterAt.includes("\n")) {
          setMentionQuery(textAfterAt);
          setShowMentions(true);
          setSelectedIndex(0);

          // Calculate dropdown position (show above textarea)
          const coordinates = getCaretCoordinates(textarea, cursorPosition);
          setMentionPosition({
            top: coordinates.top,
            left: coordinates.left,
          });
          return;
        }
      }
    }

    setShowMentions(false);
    setMentionQuery("");
  };

  // Handle keyboard navigation in mention dropdown
  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (!showMentions) {
      if (props.onKeyDown) props.onKeyDown(e);
      return;
    }

    if (e.key === "ArrowDown") {
      e.preventDefault();
      setSelectedIndex((prev) =>
        prev < filteredStaff.length - 1 ? prev + 1 : prev
      );
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      setSelectedIndex((prev) => (prev > 0 ? prev - 1 : prev));
    } else if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      if (filteredStaff[selectedIndex]) {
        insertMention(filteredStaff[selectedIndex]);
      }
    } else if (e.key === "Escape") {
      e.preventDefault();
      setShowMentions(false);
      setMentionQuery("");
    } else {
      if (props.onKeyDown) props.onKeyDown(e);
    }
  };

  // Insert selected mention into textarea
  const insertMention = (staff: Staff) => {
    const textarea = textareaRef.current;
    if (!textarea) return;

    const cursorPosition = textarea.selectionStart;
    const textBeforeCursor = textarea.value.substring(0, cursorPosition);
    const textAfterCursor = textarea.value.substring(cursorPosition);

    // Find the @ position
    const lastAtIndex = textBeforeCursor.lastIndexOf("@");
    if (lastAtIndex === -1) return;

    // Use alias if available, otherwise handle
    const mentionText = staff.alias || staff.handle;
    const newText =
      textBeforeCursor.substring(0, lastAtIndex + 1) +
      mentionText +
      " " +
      textAfterCursor;

    // Create synthetic event to trigger onChange
    const syntheticEvent = {
      target: {
        value: newText,
      },
    } as React.ChangeEvent<HTMLTextAreaElement>;

    if (onChange) onChange(syntheticEvent);

    // Update cursor position
    setTimeout(() => {
      const newCursorPos = lastAtIndex + mentionText.length + 2;
      textarea.setSelectionRange(newCursorPos, newCursorPos);
      textarea.focus();
    }, 0);

    setShowMentions(false);
    setMentionQuery("");

    if (onMentionSelect) onMentionSelect(staff);
  };

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (
        mentionsRef.current &&
        !mentionsRef.current.contains(event.target as Node) &&
        textareaRef.current &&
        !textareaRef.current.contains(event.target as Node)
      ) {
        setShowMentions(false);
      }
    };

    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  // Scroll selected item into view
  useEffect(() => {
    if (showMentions && mentionsRef.current) {
      const selectedElement = mentionsRef.current.querySelector(
        `[data-index="${selectedIndex}"]`
      );
      if (selectedElement) {
        selectedElement.scrollIntoView({ block: "nearest" });
      }
    }
  }, [selectedIndex, showMentions]);

  const getRoleIcon = (roleType: string) => {
    return roleType === "leadership" ? (
      <Shield className="h-3 w-3" />
    ) : (
      <Users className="h-3 w-3" />
    );
  };

  return (
    <div className="relative w-full flex-1">
      <Textarea
        ref={(node) => {
          // Handle both forwarded ref and internal ref
          if (typeof ref === "function") {
            ref(node);
          } else if (ref) {
            ref.current = node;
          }
          (textareaRef as any).current = node;
        }}
        value={value}
        onChange={handleTextChange}
        onKeyDown={handleKeyDown}
        className={className}
        {...props}
      />

      {/* Mention Dropdown */}
      {showMentions && filteredStaff.length > 0 && (
        <Card
          ref={mentionsRef}
          className="absolute z-50 w-72 max-h-64 overflow-y-auto shadow-lg bottom-full mb-2"
          style={{
            left: `${mentionPosition.left}px`,
          }}
        >
          <div className="p-1">
            <div className="text-xs text-muted-foreground px-2 py-1 font-medium">
              Staff Mentions
            </div>
            {filteredStaff.map((staff, index) => (
              <button
                key={staff.id}
                data-index={index}
                type="button"
                className={cn(
                  "w-full text-left px-2 py-2 rounded-sm hover:bg-accent transition-colors",
                  selectedIndex === index && "bg-accent"
                )}
                onClick={() => insertMention(staff)}
                onMouseEnter={() => setSelectedIndex(index)}
              >
                <div className="flex items-center justify-between gap-2">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-1.5 mb-0.5">
                      <span className="text-sm font-medium truncate">
                        {staff.name}
                      </span>
                      {getRoleIcon(staff.role_type)}
                    </div>
                    <div className="flex items-center gap-1 flex-wrap text-xs text-muted-foreground">
                      {staff.alias ? (
                        <>
                          <Badge
                            variant="default"
                            className="text-[10px] h-4 px-1 font-mono"
                          >
                            @{staff.alias}
                          </Badge>
                          <span>or</span>
                          <Badge
                            variant="secondary"
                            className="text-[10px] h-4 px-1 font-mono"
                          >
                            @{staff.handle}
                          </Badge>
                        </>
                      ) : (
                        <Badge
                          variant="secondary"
                          className="text-[10px] h-4 px-1 font-mono"
                        >
                          @{staff.handle}
                        </Badge>
                      )}
                    </div>
                  </div>
                  <div
                    className={`w-1.5 h-1.5 rounded-full flex-shrink-0 ${
                      staff.is_active ? "bg-green-500" : "bg-gray-400"
                    }`}
                  />
                </div>
              </button>
            ))}
          </div>
        </Card>
      )}
    </div>
  );
});

MentionTextarea.displayName = "MentionTextarea";

// Helper function to get caret coordinates
function getCaretCoordinates(
  element: HTMLTextAreaElement,
  position: number
): { top: number; left: number } {
  const div = document.createElement("div");
  const style = getComputedStyle(element);

  // Copy textarea styles to div
  Array.from(style).forEach((prop) => {
    div.style.setProperty(
      prop,
      style.getPropertyValue(prop),
      style.getPropertyPriority(prop)
    );
  });

  div.style.position = "absolute";
  div.style.visibility = "hidden";
  div.style.whiteSpace = "pre-wrap";
  div.style.wordWrap = "break-word";

  div.textContent = element.value.substring(0, position);

  const span = document.createElement("span");
  span.textContent = element.value.substring(position) || ".";
  div.appendChild(span);

  document.body.appendChild(div);

  const coordinates = {
    top: span.offsetTop,
    left: span.offsetLeft,
  };

  document.body.removeChild(div);

  return coordinates;
}
