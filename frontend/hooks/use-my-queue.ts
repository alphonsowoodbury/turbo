import { useQuery } from "@tanstack/react-query";
import * as myQueueApi from "@/lib/api/my-queue";
import type { MyQueueResponse, MyQueueCounts } from "@/lib/api/my-queue";

export function useMyQueue(limit?: number) {
  return useQuery<MyQueueResponse>({
    queryKey: ["my-queue", limit],
    queryFn: () => myQueueApi.fetchMyQueue(limit),
    refetchInterval: 30000, // Refetch every 30s to stay updated
  });
}

export function useMyQueueCounts() {
  return useQuery<MyQueueCounts>({
    queryKey: ["my-queue", "counts"],
    queryFn: () => myQueueApi.fetchMyQueueCounts(),
    refetchInterval: 30000, // Refetch every 30s to update badge counts
  });
}

export function useReviewRequests(limit?: number) {
  return useQuery({
    queryKey: ["my-queue", "review-requests", limit],
    queryFn: () => myQueueApi.fetchReviewRequests(limit),
    refetchInterval: 30000,
  });
}
