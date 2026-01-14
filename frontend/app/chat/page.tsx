"use client";

import { Suspense, useState, useEffect } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { useStaff } from "@/hooks/use-staff";
import { StaffChat } from "@/components/staff/staff-chat";
import { Card } from "@/components/ui/card";
import { MessageSquare, Users } from "lucide-react";
import { Input } from "@/components/ui/input";
import { Search } from "lucide-react";

interface ChatItem {
  id: string;
  name: string;
  handle?: string;
  role?: string;
  description?: string;
  is_active?: boolean;
}

function ChatContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const idFromUrl = searchParams.get("id");

  const [selectedId, setSelectedId] = useState<string | null>(idFromUrl);
  const [searchQuery, setSearchQuery] = useState("");

  const { data: allStaff = [], isLoading } = useStaff();

  // Sync URL with selection
  useEffect(() => {
    if (idFromUrl && idFromUrl !== selectedId) {
      setSelectedId(idFromUrl);
    }
  }, [idFromUrl, selectedId]);

  const handleSelect = (id: string) => {
    setSelectedId(id);
    router.push(`/chat?id=${id}`, { scroll: false });
  };

  // Map staff to chat items
  const staffItems: ChatItem[] = allStaff.map((s) => ({
    id: s.id,
    name: s.name,
    handle: s.handle,
    role: s.role_type,
    description: s.persona?.substring(0, 100),
    is_active: s.is_active,
  }));

  // Filter items
  const filteredItems = staffItems.filter((item) =>
    item.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    item.description?.toLowerCase().includes(searchQuery.toLowerCase()) ||
    item.handle?.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <div className="flex h-[calc(100vh-3.5rem)] bg-background">
      {/* Left Sidebar - Unified List */}
      <div className="w-80 border-r flex-shrink-0 flex flex-col">
        {/* Header */}
        <div className="p-4 border-b">
          <h2 className="font-semibold mb-3">Conversations</h2>
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
            <Input
              placeholder="Search..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-9"
            />
          </div>
        </div>

        {/* List */}
        <div className="flex-1 overflow-y-auto">
          {isLoading ? (
            <div className="p-4 text-center text-muted-foreground">
              Loading...
            </div>
          ) : filteredItems.length === 0 ? (
            <div className="p-8 text-center">
              <MessageSquare className="h-12 w-12 mx-auto mb-4 text-muted-foreground" />
              <p className="text-sm text-muted-foreground">
                {searchQuery ? "No matches found" : "No conversations available"}
              </p>
            </div>
          ) : (
            <div className="divide-y">
              {filteredItems.map((item) => (
                <button
                  key={item.id}
                  onClick={() => handleSelect(item.id)}
                  className={`w-full p-4 text-left hover:bg-accent transition-colors ${
                    selectedId === item.id
                      ? "bg-accent border-l-2 border-primary"
                      : ""
                  }`}
                >
                  <div className="flex items-start gap-3">
                    <div className="mt-1">
                      <div className="h-8 w-8 rounded-full bg-blue-100 dark:bg-blue-900 flex items-center justify-center">
                        <Users className="h-4 w-4 text-blue-600 dark:text-blue-400" />
                      </div>
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2">
                        <h3 className="font-medium truncate">{item.name}</h3>
                        {item.is_active && (
                          <span className="h-2 w-2 rounded-full bg-green-500" />
                        )}
                      </div>
                      {item.handle && (
                        <p className="text-xs text-muted-foreground">@{item.handle}</p>
                      )}
                      {item.description && (
                        <p className="text-xs text-muted-foreground mt-1 line-clamp-2">
                          {item.description}
                        </p>
                      )}
                      {item.role && (
                        <div className="flex items-center gap-2 mt-1">
                          <span className="text-xs px-2 py-0.5 rounded-full bg-muted">
                            {item.role.replace(/_/g, " ")}
                          </span>
                        </div>
                      )}
                    </div>
                  </div>
                </button>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col">
        {selectedId ? (
          <StaffChat staffId={selectedId} />
        ) : (
          <div className="flex-1 flex items-center justify-center">
            <Card className="p-12 text-center">
              <MessageSquare className="h-16 w-16 mx-auto mb-4 text-muted-foreground" />
              <h3 className="text-lg font-semibold mb-2">No Chat Selected</h3>
              <p className="text-sm text-muted-foreground max-w-md">
                Select a staff member from the sidebar to start chatting
              </p>
            </Card>
          </div>
        )}
      </div>
    </div>
  );
}

export default function ChatPage() {
  return (
    <Suspense fallback={
      <div className="flex h-[calc(100vh-3.5rem)] items-center justify-center">
        <div className="text-muted-foreground">Loading chat...</div>
      </div>
    }>
      <ChatContent />
    </Suspense>
  );
}
