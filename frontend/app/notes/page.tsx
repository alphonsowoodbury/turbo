"use client";

import { useState, useEffect, useMemo, Suspense } from "react";
import { useSearchParams } from "next/navigation";
import { PageLayout } from "@/components/layout/page-layout";
import { Card, CardContent } from "@/components/ui/card";
import { useNotes } from "@/hooks/use-notes";
import { useWorkspace, getWorkspaceParams } from "@/hooks/use-workspace";
import { MarkdownRenderer } from "@/components/ui/markdown-renderer";
import { CollapsibleInfoPanel } from "@/components/shared/collapsible-info-panel";
import { StickyNote, Calendar, FolderOpen, Star, ChevronRight, ChevronDown, Filter, X, Archive } from "lucide-react";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Separator } from "@/components/ui/separator";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import { useIsFavorite, useToggleFavorite } from "@/hooks/use-favorites";
import { SubagentButton } from "@/components/subagent/subagent-button";
import { EntityCommentsSection } from "@/components/shared/entity-comments-section";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

interface Note {
  id: string;
  title: string;
  content: string | null;
  workspace: string;
  work_company: string | null;
  is_archived: boolean;
  created_at: string;
  updated_at: string;
  tags: Array<{ id: string; name: string; color: string }>;
}

function NotesContent() {
  const searchParams = useSearchParams();
  const noteIdFromUrl = searchParams.get("id");

  const [selectedNote, setSelectedNote] = useState<Note | null>(null);
  const [notesExpanded, setNotesExpanded] = useState(true);
  const [isFilterOpen, setIsFilterOpen] = useState(false);

  // Filter states
  const [selectedWorkspace, setSelectedWorkspace] = useState<string>("all");
  const [showArchived, setShowArchived] = useState(false);
  const [sortBy, setSortBy] = useState<string>("updated");

  const { workspace, workCompany } = useWorkspace();
  const workspaceParams = getWorkspaceParams(workspace, workCompany);

  const { data: allNotes, isLoading } = useNotes({
    ...workspaceParams,
    include_archived: showArchived,
  });

  const isFavorited = useIsFavorite("note", selectedNote?.id || "");
  const { toggle: toggleFavorite, isPending } = useToggleFavorite();

  // Apply filters
  const filteredNotes = useMemo(() => {
    if (!allNotes) return [];

    let filtered = allNotes;

    if (selectedWorkspace !== "all") {
      filtered = filtered.filter((n) => n.workspace === selectedWorkspace);
    }

    return filtered;
  }, [allNotes, selectedWorkspace]);

  // Sort notes
  const sortedNotes = useMemo(() => {
    const sorted = [...filteredNotes];

    switch (sortBy) {
      case "updated":
        return sorted.sort((a, b) => new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime());
      case "created":
        return sorted.sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime());
      case "title":
        return sorted.sort((a, b) => a.title.localeCompare(b.title));
      default:
        return sorted;
    }
  }, [filteredNotes, sortBy]);

  const hasActiveFilters = selectedWorkspace !== "all" || showArchived;

  const clearFilters = () => {
    setSelectedWorkspace("all");
    setShowArchived(false);
  };

  const notes = sortedNotes;

  // Auto-select note from URL
  useEffect(() => {
    if (noteIdFromUrl && notes) {
      const note = notes.find((n) => n.id === noteIdFromUrl);
      if (note) {
        setSelectedNote(note);
        setNotesExpanded(true);
      }
    }
  }, [noteIdFromUrl, notes]);

  const handleFavoriteClick = () => {
    if (selectedNote) {
      toggleFavorite("note", selectedNote.id, isFavorited);
    }
  };

  // Toggle button for collapsible filter panel
  const toggleButton = (
    <Button
      variant="ghost"
      size="sm"
      onClick={() => setIsFilterOpen(!isFilterOpen)}
      className="h-8 w-8 p-0"
      aria-label={isFilterOpen ? "Hide filters" : "Show filters"}
    >
      <ChevronDown
        className={cn(
          "h-4 w-4 transition-transform duration-250",
          isFilterOpen && "rotate-180"
        )}
      />
    </Button>
  );

  return (
    <PageLayout
      title="Notes"
      isLoading={isLoading}
      titleControl={toggleButton}
      createLabel="New Note"
      onCreateClick={() => {
        console.log("Create note clicked");
      }}
    >
      {/* Collapsible Filter Panel */}
      <CollapsibleInfoPanel
        isOpen={isFilterOpen}
        onToggle={setIsFilterOpen}
        storageKey="notes-filter-panel"
      >
        <div className="px-6 py-4 bg-muted/30 border-b">
          {/* All Controls in One Row */}
          <div className="flex items-center justify-between gap-4">
            {/* Filter Controls */}
            <div className="flex items-center gap-3 flex-1">
              <span className="text-sm font-medium text-muted-foreground">Filters:</span>

              <Select value={selectedWorkspace} onValueChange={setSelectedWorkspace}>
                <SelectTrigger className="w-40 h-8">
                  <SelectValue placeholder="Workspace" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Workspaces</SelectItem>
                  <SelectItem value="personal">Personal</SelectItem>
                  <SelectItem value="freelance">Freelance</SelectItem>
                  <SelectItem value="work">Work</SelectItem>
                </SelectContent>
              </Select>

              <Button
                variant={showArchived ? "default" : "outline"}
                size="sm"
                onClick={() => setShowArchived(!showArchived)}
              >
                <Archive className="h-4 w-4 mr-1" />
                {showArchived ? "Hide Archived" : "Show Archived"}
              </Button>

              {hasActiveFilters && (
                <Button variant="ghost" size="sm" onClick={clearFilters}>
                  <X className="h-4 w-4 mr-1" />
                  Clear
                </Button>
              )}
            </div>

            {/* Sort Controls */}
            <div className="flex items-center gap-3">
              <span className="text-sm font-medium text-muted-foreground">Sort:</span>
              <Select value={sortBy} onValueChange={setSortBy}>
                <SelectTrigger className="w-32 h-8">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="updated">Updated</SelectItem>
                  <SelectItem value="created">Created</SelectItem>
                  <SelectItem value="title">Title</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
        </div>
      </CollapsibleInfoPanel>

      <div className="flex h-[calc(100vh-120px)] overflow-hidden">
        {/* Vertical Tab Bar */}
        <div className="flex flex-col bg-muted/30 border-r">
          {/* Notes Tab */}
          <button
            onClick={() => setNotesExpanded(!notesExpanded)}
            className={cn(
              "flex items-center justify-center px-2 py-4 hover:bg-accent transition-colors",
              notesExpanded && "bg-accent"
            )}
            style={{ writingMode: "vertical-rl" }}
          >
            <span className="text-xs font-medium tracking-wide">NOTES</span>
          </button>
        </div>

        {/* Notes Panel */}
        <div
          className={cn(
            "transition-all duration-300 border-r overflow-hidden",
            notesExpanded ? "w-80" : "w-0"
          )}
        >
          <div className="h-full flex flex-col">
            <div className="flex items-center justify-between p-4 border-b">
              <div className="flex items-center gap-2">
                <StickyNote className="h-5 w-5" />
                <span className="font-semibold">Notes ({notes?.length || 0})</span>
              </div>
              <Button
                variant="ghost"
                size="icon"
                onClick={() => setNotesExpanded(false)}
                className="h-8 w-8"
              >
                <ChevronRight className="h-4 w-4" />
              </Button>
            </div>
            <ScrollArea className="flex-1">
              {isLoading && (
                <p className="text-sm text-muted-foreground p-4">Loading...</p>
              )}

              {notes && notes.length === 0 && (
                <p className="text-sm text-muted-foreground p-4">
                  No notes found
                </p>
              )}

              {notes?.map((note) => (
                <div key={note.id}>
                  <button
                    onClick={() => setSelectedNote(note)}
                    className={cn(
                      "w-full text-left p-4 hover:bg-accent transition-colors",
                      selectedNote?.id === note.id && "bg-accent"
                    )}
                  >
                    <div className="flex items-start justify-between gap-2 mb-1">
                      <h3 className="font-medium text-sm line-clamp-1 flex-1">
                        {note.title}
                      </h3>
                      {note.is_archived && (
                        <Archive className="h-3 w-3 text-muted-foreground flex-shrink-0" />
                      )}
                    </div>
                    <div className="flex items-center gap-2 flex-wrap">
                      <span className="text-xs px-2 py-0.5 rounded-full bg-primary/10 text-primary">
                        {note.workspace}
                      </span>
                      {note.tags.map((tag) => (
                        <span
                          key={tag.id}
                          className="text-xs px-2 py-0.5 rounded-full"
                          style={{
                            backgroundColor: `${tag.color}20`,
                            color: tag.color,
                          }}
                        >
                          {tag.name}
                        </span>
                      ))}
                      <span className="text-xs text-muted-foreground flex items-center gap-1">
                        <Calendar className="h-3 w-3" />
                        {new Date(note.created_at).toLocaleDateString()}
                      </span>
                    </div>
                  </button>
                  <Separator />
                </div>
              ))}
            </ScrollArea>
          </div>
        </div>

        {/* Note Viewer */}
        <div className="flex-1 overflow-hidden">
          {selectedNote ? (
            <div className="h-full flex flex-col overflow-hidden">
              {/* Scrollable Content Area */}
              <div className="flex-1 overflow-y-auto">
                <div className="border-b p-6">
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-2">
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={handleFavoriteClick}
                          disabled={isPending}
                        >
                          <Star
                            className={cn(
                              "h-4 w-4",
                              isFavorited && "fill-yellow-400 text-yellow-400"
                            )}
                          />
                        </Button>
                        <SubagentButton
                          context={{ note_id: selectedNote.id }}
                          suggestedAgent="note-organizer"
                          suggestedPrompt="Help me organize and expand this note with related ideas and action items."
                          size="sm"
                        />
                      </div>
                      <h1 className="text-2xl font-bold">{selectedNote.title}</h1>
                      <div className="flex items-center gap-3 mt-2 text-sm text-muted-foreground flex-wrap">
                        <span className="flex items-center gap-1">
                          <FolderOpen className="h-4 w-4" />
                          {selectedNote.workspace}
                        </span>
                        {selectedNote.work_company && (
                          <span>{selectedNote.work_company}</span>
                        )}
                        {selectedNote.is_archived && (
                          <Badge variant="secondary">
                            <Archive className="h-3 w-3 mr-1" />
                            Archived
                          </Badge>
                        )}
                        <span className="flex items-center gap-1">
                          <Calendar className="h-4 w-4" />
                          Updated {new Date(selectedNote.updated_at).toLocaleDateString()}
                        </span>
                      </div>
                      {selectedNote.tags.length > 0 && (
                        <div className="flex items-center gap-2 mt-3">
                          {selectedNote.tags.map((tag) => (
                            <Badge
                              key={tag.id}
                              variant="outline"
                              style={{
                                borderColor: tag.color,
                                color: tag.color,
                              }}
                            >
                              {tag.name}
                            </Badge>
                          ))}
                        </div>
                      )}
                    </div>
                  </div>
                </div>
                <div className="p-6">
                  {selectedNote.content ? (
                    <MarkdownRenderer content={selectedNote.content} />
                  ) : (
                    <p className="text-muted-foreground italic">No content</p>
                  )}
                </div>
              </div>

              {/* Collapsible & Resizable Comments Section */}
              <EntityCommentsSection
                entityType="note"
                entityId={selectedNote.id}
                defaultHeight={500}
                minHeight={200}
                maxHeight={800}
              />
            </div>
          ) : (
            <div className="flex items-center justify-center h-full">
              <div className="text-center text-muted-foreground">
                <StickyNote className="h-16 w-16 mx-auto mb-4 opacity-20" />
                <p>Select a note to view</p>
              </div>
            </div>
          )}
        </div>
      </div>
    </PageLayout>
  );
}

export default function NotesPage() {
  return (
    <Suspense fallback={
      <PageLayout title="Notes" isLoading={true}>
        <div className="p-6">
          <p>Loading notes...</p>
        </div>
      </PageLayout>
    }>
      <NotesContent />
    </Suspense>
  );
}
