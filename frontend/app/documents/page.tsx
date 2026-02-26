"use client";

import { useState, useEffect, useMemo, Suspense } from "react";
import { useSearchParams } from "next/navigation";
import { PageLayout } from "@/components/layout/page-layout";
import { Card, CardContent } from "@/components/ui/card";
import { useDocuments } from "@/hooks/use-documents";
import { useProjects } from "@/hooks/use-projects";
import { useWorkspace, getWorkspaceParams } from "@/hooks/use-workspace";
import { MarkdownRenderer } from "@/components/ui/markdown-renderer";
import { TableOfContents } from "@/components/ui/table-of-contents";
import { CollapsibleInfoPanel } from "@/components/shared/collapsible-info-panel";
import { FileText, Calendar, FolderOpen, Star, ChevronRight, ChevronDown, Filter, X } from "lucide-react";
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

interface Document {
  id: string;
  title: string;
  content: string;
  type: string;
  format: string;
  version: string | null;
  author: string | null;
  project_id: string;
  created_at: string;
  updated_at: string;
}

function DocumentsContent() {
  const searchParams = useSearchParams();
  const documentIdFromUrl = searchParams.get("id");

  const [selectedDoc, setSelectedDoc] = useState<Document | null>(null);
  const [documentsExpanded, setDocumentsExpanded] = useState(true);
  const [tocExpanded, setTocExpanded] = useState(false);
  const [isFilterOpen, setIsFilterOpen] = useState(false);

  // Filter states
  const [selectedProject, setSelectedProject] = useState<string>("all");
  const [selectedType, setSelectedType] = useState<string>("all");
  const [selectedFormat, setSelectedFormat] = useState<string>("all");
  const [groupBy, setGroupBy] = useState<string>("none");
  const [sortBy, setSortBy] = useState<string>("updated");

  const { workspace, workCompany } = useWorkspace();
  const workspaceParams = getWorkspaceParams(workspace, workCompany);

  const { data: allDocuments, isLoading } = useDocuments(workspaceParams);
  const { data: projects } = useProjects(workspaceParams);

  const isFavorited = useIsFavorite("document", selectedDoc?.id || "");
  const { toggle: toggleFavorite, isPending } = useToggleFavorite();

  // Apply filters
  const filteredDocuments = useMemo(() => {
    if (!allDocuments) return [];

    let filtered = allDocuments;

    if (selectedProject !== "all") {
      filtered = filtered.filter((d) => d.project_id === selectedProject);
    }

    if (selectedType !== "all") {
      filtered = filtered.filter((d) => d.type === selectedType);
    }

    if (selectedFormat !== "all") {
      filtered = filtered.filter((d) => d.format === selectedFormat);
    }

    return filtered;
  }, [allDocuments, selectedProject, selectedType, selectedFormat]);

  // Sort documents
  const sortedDocuments = useMemo(() => {
    const sorted = [...filteredDocuments];

    switch (sortBy) {
      case "updated":
        return sorted.sort((a, b) => new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime());
      case "created":
        return sorted.sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime());
      case "title":
        return sorted.sort((a, b) => a.title.localeCompare(b.title));
      case "type":
        return sorted.sort((a, b) => a.type.localeCompare(b.type));
      default:
        return sorted;
    }
  }, [filteredDocuments, sortBy]);

  // Group documents
  const groupedDocuments = useMemo(() => {
    if (groupBy === "none") {
      return { "All Documents": sortedDocuments };
    }

    const groups: Record<string, typeof sortedDocuments> = {};

    sortedDocuments.forEach((doc) => {
      let key = "";

      if (groupBy === "project") {
        const project = projects?.find((p) => p.id === doc.project_id);
        key = project?.name || "Unknown Project";
      } else if (groupBy === "type") {
        key = doc.type;
      } else if (groupBy === "format") {
        key = doc.format;
      }

      if (!groups[key]) {
        groups[key] = [];
      }
      groups[key].push(doc);
    });

    return groups;
  }, [sortedDocuments, groupBy, projects]);

  const hasActiveFilters = selectedProject !== "all" || selectedType !== "all" || selectedFormat !== "all";

  const clearFilters = () => {
    setSelectedProject("all");
    setSelectedType("all");
    setSelectedFormat("all");
  };

  const documents = sortedDocuments;

  // Auto-select document from URL
  useEffect(() => {
    if (documentIdFromUrl && documents) {
      const doc = documents.find((d) => d.id === documentIdFromUrl);
      if (doc) {
        setSelectedDoc(doc);
        setDocumentsExpanded(true); // Expand to show selection
      }
    }
  }, [documentIdFromUrl, documents]);

  const handleFavoriteClick = () => {
    if (selectedDoc) {
      toggleFavorite("document", selectedDoc.id, isFavorited);
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
      title="Documents"
      isLoading={isLoading}
      titleControl={toggleButton}
      createLabel="New Document"
      onCreateClick={() => {
        console.log("Create document clicked");
      }}
    >
      {/* Collapsible Filter Panel */}
      <CollapsibleInfoPanel
        isOpen={isFilterOpen}
        onToggle={setIsFilterOpen}
        storageKey="documents-filter-panel"
      >
        <div className="px-6 py-4 bg-muted/30 border-b">
          {/* All Controls in One Row */}
          <div className="flex items-center justify-between gap-4">
            {/* Filter Controls */}
            <div className="flex items-center gap-3 flex-1">
              <span className="text-sm font-medium text-muted-foreground">Filters:</span>

              <Select value={selectedProject} onValueChange={setSelectedProject}>
                <SelectTrigger className="w-40 h-8">
                  <SelectValue placeholder="Project" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Projects</SelectItem>
                  {projects?.map((project) => (
                    <SelectItem key={project.id} value={project.id}>
                      {project.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>

              <Select value={selectedType} onValueChange={setSelectedType}>
                <SelectTrigger className="w-40 h-8">
                  <SelectValue placeholder="Type" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Types</SelectItem>
                  <SelectItem value="specification">Specification</SelectItem>
                  <SelectItem value="user_guide">User Guide</SelectItem>
                  <SelectItem value="api_doc">API Doc</SelectItem>
                  <SelectItem value="readme">README</SelectItem>
                  <SelectItem value="changelog">Changelog</SelectItem>
                  <SelectItem value="requirements">Requirements</SelectItem>
                  <SelectItem value="design">Design</SelectItem>
                  <SelectItem value="other">Other</SelectItem>
                </SelectContent>
              </Select>

              <Select value={selectedFormat} onValueChange={setSelectedFormat}>
                <SelectTrigger className="w-40 h-8">
                  <SelectValue placeholder="Format" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Formats</SelectItem>
                  <SelectItem value="markdown">Markdown</SelectItem>
                  <SelectItem value="html">HTML</SelectItem>
                  <SelectItem value="text">Text</SelectItem>
                  <SelectItem value="pdf">PDF</SelectItem>
                  <SelectItem value="docx">DOCX</SelectItem>
                </SelectContent>
              </Select>

              {hasActiveFilters && (
                <Button variant="ghost" size="sm" onClick={clearFilters}>
                  <X className="h-4 w-4 mr-1" />
                  Clear
                </Button>
              )}
            </div>

            {/* Sort and Group Controls */}
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
                  <SelectItem value="type">Type</SelectItem>
                </SelectContent>
              </Select>

              <span className="text-sm font-medium text-muted-foreground">Group:</span>
              <Select value={groupBy} onValueChange={setGroupBy}>
                <SelectTrigger className="w-32 h-8">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="none">None</SelectItem>
                  <SelectItem value="project">Project</SelectItem>
                  <SelectItem value="type">Type</SelectItem>
                  <SelectItem value="format">Format</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
        </div>
      </CollapsibleInfoPanel>

      <div className="flex h-[calc(100vh-120px)] overflow-hidden">
        {/* Vertical Tab Bar */}
        <div className="flex flex-col bg-muted/30 border-r">
          {/* Documents Tab */}
          <button
            onClick={() => setDocumentsExpanded(!documentsExpanded)}
            className={cn(
              "flex items-center justify-center px-2 py-4 hover:bg-accent transition-colors border-b",
              documentsExpanded && "bg-accent"
            )}
            style={{ writingMode: "vertical-rl" }}
          >
            <span className="text-xs font-medium tracking-wide">DOCUMENTS</span>
          </button>

          {/* Table of Contents Tab */}
          {selectedDoc && (
            <button
              onClick={() => setTocExpanded(!tocExpanded)}
              className={cn(
                "flex items-center justify-center px-2 py-4 hover:bg-accent transition-colors",
                tocExpanded && "bg-accent"
              )}
              style={{ writingMode: "vertical-rl" }}
            >
              <span className="text-xs font-medium tracking-wide">TABLE OF CONTENTS</span>
            </button>
          )}
        </div>

        {/* Documents Panel */}
        <div
          className={cn(
            "transition-all duration-300 border-r overflow-hidden",
            documentsExpanded ? "w-80" : "w-0"
          )}
        >
          <div className="h-full flex flex-col">
            <div className="flex items-center justify-between p-4 border-b">
              <div className="flex items-center gap-2">
                <FileText className="h-5 w-5" />
                <span className="font-semibold">Documents ({documents?.length || 0})</span>
              </div>
              <Button
                variant="ghost"
                size="icon"
                onClick={() => setDocumentsExpanded(false)}
                className="h-8 w-8"
              >
                <ChevronRight className="h-4 w-4" />
              </Button>
            </div>
            <ScrollArea className="flex-1">
              {isLoading && (
                <p className="text-sm text-muted-foreground p-4">Loading...</p>
              )}

              {documents && documents.length === 0 && (
                <p className="text-sm text-muted-foreground p-4">
                  No documents found
                </p>
              )}

              {documents?.map((doc) => (
                <div key={doc.id}>
                  <button
                    onClick={() => setSelectedDoc(doc)}
                    className={cn(
                      "w-full text-left p-4 hover:bg-accent transition-colors",
                      selectedDoc?.id === doc.id && "bg-accent"
                    )}
                  >
                    <h3 className="font-medium text-sm line-clamp-1">
                      {doc.title}
                    </h3>
                    <div className="flex items-center gap-2 mt-1">
                      <span className="text-xs px-2 py-0.5 rounded-full bg-primary/10 text-primary">
                        {doc.type}
                      </span>
                      <span className="text-xs text-muted-foreground flex items-center gap-1">
                        <Calendar className="h-3 w-3" />
                        {new Date(doc.created_at).toLocaleDateString()}
                      </span>
                    </div>
                  </button>
                  <Separator />
                </div>
              ))}
            </ScrollArea>
          </div>
        </div>

        {/* Table of Contents Panel */}
        {selectedDoc && (
          <div
            className={cn(
              "transition-all duration-300 border-r overflow-hidden",
              tocExpanded ? "w-64" : "w-0"
            )}
          >
            <div className="h-full flex flex-col">
              <div className="flex items-center justify-between p-4 border-b">
                <span className="font-semibold text-sm">Table of Contents</span>
                <Button
                  variant="ghost"
                  size="icon"
                  onClick={() => setTocExpanded(false)}
                  className="h-8 w-8"
                >
                  <ChevronRight className="h-4 w-4" />
                </Button>
              </div>
              <ScrollArea className="flex-1 p-2">
                <TableOfContents content={selectedDoc.content} />
              </ScrollArea>
            </div>
          </div>
        )}

        {/* Document Viewer */}
        <div className="flex-1 overflow-hidden">
          {selectedDoc ? (
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
                          context={{ document_id: selectedDoc.id }}
                          suggestedAgent="doc-curator"
                          suggestedPrompt="Review this document for clarity, completeness, and suggest improvements."
                          size="sm"
                        />
                      </div>
                      <h1 className="text-2xl font-bold">{selectedDoc.title}</h1>
                      <div className="flex items-center gap-3 mt-2 text-sm text-muted-foreground">
                        <span className="flex items-center gap-1">
                          <FolderOpen className="h-4 w-4" />
                          {selectedDoc.type}
                        </span>
                        {selectedDoc.version && (
                          <span>Version {selectedDoc.version}</span>
                        )}
                        <span className="flex items-center gap-1">
                          <Calendar className="h-4 w-4" />
                          Updated {new Date(selectedDoc.updated_at).toLocaleDateString()}
                        </span>
                      </div>
                    </div>
                  </div>
                </div>
                <div className="p-6">
                  <MarkdownRenderer content={selectedDoc.content} />
                </div>
              </div>

              {/* Collapsible & Resizable Comments Section */}
              <EntityCommentsSection
                entityType="document"
                entityId={selectedDoc.id}
                defaultHeight={500}
                minHeight={200}
                maxHeight={800}
              />
            </div>
          ) : (
            <div className="flex items-center justify-center h-full">
              <div className="text-center text-muted-foreground">
                <FileText className="h-16 w-16 mx-auto mb-4 opacity-20" />
                <p>Select a document to view</p>
              </div>
            </div>
          )}
        </div>
      </div>
    </PageLayout>
  );
}

export default function DocumentsPage() {
  return (
    <Suspense fallback={
      <PageLayout title="Documents" isLoading={true}>
        <div className="page-padding">
          <p>Loading documents...</p>
        </div>
      </PageLayout>
    }>
      <DocumentsContent />
    </Suspense>
  );
}
