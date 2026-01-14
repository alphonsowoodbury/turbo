import { useQuery } from "@tanstack/react-query";
import { scriptsApi } from "@/lib/api/scripts";

export function useScriptRuns(params?: {
  script_name?: string;
  status?: string;
  limit?: number;
  offset?: number;
}) {
  return useQuery({
    queryKey: ["scripts", "runs", params],
    queryFn: () => scriptsApi.list(params),
    refetchInterval: 5000, // Poll every 5 seconds
  });
}

export function useScriptRun(scriptRunId: string | null) {
  return useQuery({
    queryKey: ["scripts", "run", scriptRunId],
    queryFn: () => scriptsApi.get(scriptRunId!),
    enabled: !!scriptRunId,
  });
}

export function useRunningScripts() {
  return useQuery({
    queryKey: ["scripts", "running"],
    queryFn: () => scriptsApi.getRunning(),
    refetchInterval: 3000, // Poll every 3 seconds
  });
}

export function useRecentScripts(limit: number = 50) {
  return useQuery({
    queryKey: ["scripts", "recent", limit],
    queryFn: () => scriptsApi.getRecent(limit),
    refetchInterval: 5000, // Poll every 5 seconds
  });
}
