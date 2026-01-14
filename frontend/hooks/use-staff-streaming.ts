import { useState, useCallback, useRef } from "react";
import { useQueryClient } from "@tanstack/react-query";

const API_BASE = "http://localhost:8001/api/v1";

interface StreamEvent {
  type: "token" | "done" | "error";
  content?: string;
  message_id?: string;
  detail?: string;
}

interface UseStaffStreamingReturn {
  sendMessage: (content: string) => Promise<void>;
  isStreaming: boolean;
  streamingContent: string;
  error: string | null;
  abortStream: () => void;
}

/**
 * Hook for streaming staff messages via Server-Sent Events (SSE)
 *
 * Usage:
 * ```tsx
 * const { sendMessage, isStreaming, streamingContent, error } = useStaffStreaming(staffId);
 *
 * // Send a message and receive streaming response
 * await sendMessage("Hello!");
 * // streamingContent will update in real-time as tokens arrive
 * ```
 */
export function useStaffStreaming(staffId: string): UseStaffStreamingReturn {
  const [isStreaming, setIsStreaming] = useState(false);
  const [streamingContent, setStreamingContent] = useState("");
  const [error, setError] = useState<string | null>(null);
  const abortControllerRef = useRef<AbortController | null>(null);
  const queryClient = useQueryClient();

  const abortStream = useCallback(() => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      abortControllerRef.current = null;
      setIsStreaming(false);
    }
  }, []);

  const sendMessage = useCallback(
    async (content: string) => {
      // Reset state
      setIsStreaming(true);
      setStreamingContent("");
      setError(null);

      // Create abort controller for this stream
      const abortController = new AbortController();
      abortControllerRef.current = abortController;

      try {
        const response = await fetch(
          `${API_BASE}/staff/${staffId}/messages/stream`,
          {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
            },
            body: JSON.stringify({ content }),
            signal: abortController.signal,
          }
        );

        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }

        if (!response.body) {
          throw new Error("Response body is null");
        }

        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let buffer = "";

        while (true) {
          const { done, value } = await reader.read();

          if (done) {
            break;
          }

          // Decode and add to buffer
          buffer += decoder.decode(value, { stream: true });

          // Process complete events
          const lines = buffer.split("\n");
          buffer = lines.pop() || ""; // Keep incomplete line in buffer

          for (const line of lines) {
            if (line.startsWith("data: ")) {
              try {
                const data: StreamEvent = JSON.parse(line.slice(6));

                if (data.type === "token" && data.content) {
                  // Update streaming content progressively
                  setStreamingContent((prev) => prev + data.content);
                } else if (data.type === "done") {
                  // Stream complete - invalidate all conversation queries for this staff
                  // Use partial matching to catch all variants (with/without params)
                  await queryClient.invalidateQueries({
                    queryKey: ["staff", staffId, "conversation"],
                    exact: false,
                  });

                  // Manually trigger refetch and wait for it
                  await queryClient.refetchQueries({
                    queryKey: ["staff", staffId, "conversation"],
                    exact: false,
                  });

                  // Only clear after refetch completes
                  setTimeout(() => setStreamingContent(""), 100);
                } else if (data.type === "error") {
                  setError(data.detail || "An error occurred");
                }
              } catch (parseError) {
                console.warn("Failed to parse SSE event:", line, parseError);
              }
            }
          }
        }
      } catch (err) {
        if (err instanceof Error) {
          if (err.name === "AbortError") {
            // User cancelled - not an error
            console.log("Stream aborted by user");
          } else {
            setError(err.message);
          }
        } else {
          setError("An unknown error occurred");
        }
      } finally {
        setIsStreaming(false);
        abortControllerRef.current = null;
      }
    },
    [staffId, queryClient]
  );

  return {
    sendMessage,
    isStreaming,
    streamingContent,
    error,
    abortStream,
  };
}
