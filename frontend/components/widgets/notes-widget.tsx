"use client";

import { useState } from "react";
import { Plus, X } from "lucide-react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

interface Note {
  id: string;
  text: string;
  createdAt: Date;
}

export function NotesWidget() {
  const [notes, setNotes] = useState<Note[]>([]);
  const [inputValue, setInputValue] = useState("");

  const handleAddNote = () => {
    if (inputValue.trim()) {
      const newNote: Note = {
        id: Date.now().toString(),
        text: inputValue.trim(),
        createdAt: new Date(),
      };
      setNotes([newNote, ...notes]);
      setInputValue("");
    }
  };

  const handleDeleteNote = (id: string) => {
    setNotes(notes.filter((note) => note.id !== id));
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleAddNote();
    }
  };

  return (
    <div className="space-y-3">
      {/* Input Area */}
      <div className="space-y-2">
        <textarea
          value={inputValue}
          onChange={(e) => setInputValue(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Quick note... (Enter to save)"
          className={cn(
            "w-full px-3 py-2 bg-background border rounded-lg resize-none",
            "focus:outline-none focus:ring-2 focus:ring-primary text-sm",
            "min-h-[60px]"
          )}
        />
        <Button
          onClick={handleAddNote}
          size="sm"
          className="w-full"
          disabled={!inputValue.trim()}
        >
          <Plus className="h-4 w-4 mr-1" />
          Add Note
        </Button>
      </div>

      {/* Notes List */}
      <div className="space-y-2">
        {notes.length === 0 ? (
          <div className="text-xs text-muted-foreground text-center py-4">
            No notes yet. Add a quick note above!
          </div>
        ) : (
          <div className="space-y-2 max-h-[300px] overflow-y-auto">
            {notes.map((note) => (
              <div
                key={note.id}
                className="group relative p-3 bg-muted/50 rounded-lg border hover:bg-muted transition-colors"
              >
                <button
                  onClick={() => handleDeleteNote(note.id)}
                  className={cn(
                    "absolute top-2 right-2 p-1 rounded hover:bg-background",
                    "opacity-0 group-hover:opacity-100 transition-opacity"
                  )}
                >
                  <X className="h-3 w-3 text-muted-foreground" />
                </button>
                <p className="text-xs whitespace-pre-wrap pr-6">{note.text}</p>
                <div className="text-[10px] text-muted-foreground mt-1">
                  {note.createdAt.toLocaleString()}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {notes.length > 0 && (
        <div className="text-[10px] text-muted-foreground text-center">
          {notes.length} {notes.length === 1 ? "note" : "notes"}
        </div>
      )}
    </div>
  );
}
