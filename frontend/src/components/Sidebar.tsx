import { useMutation } from "@tanstack/react-query";
import { Play, Square } from "lucide-react";
import { api } from "../api/client";
import { useRunStore } from "../store/runStore";
import { Button } from "./ui/button";

export function Sidebar() {
  const view = useRunStore((s) => s.view());
  const rootAgentId = useRunStore((s) => s.rootAgentId);
  const startNewRun = useRunStore((s) => s.startNewRun);

  const startMutation = useMutation({
    mutationFn: () => api.startProcessing(),
    onSuccess: (result) => {
      if (!result.started) return;
      startNewRun(result.sender_email);
    },
  });
  const stopMutation = useMutation({
    mutationFn: () => api.stopAgent(rootAgentId!),
  });

  const idle = view === "idle" || view === "completed" || view === "failed";

  return (
    <div className="flex items-center gap-3 border-b border-neutral-border bg-surface px-6 py-4">
      {idle ? (
        <Button onClick={() => startMutation.mutate()} disabled={startMutation.isPending}>
          <Play className="h-4 w-4" strokeWidth={2.5} />
          Start claims processing
        </Button>
      ) : (
        <>
          <Button variant="outline" disabled>
            <span className="h-2 w-2 animate-pulse rounded-full bg-info-fg" />
            Processing…
          </Button>
          <Button variant="danger" onClick={() => stopMutation.mutate()} disabled={stopMutation.isPending}>
            <Square className="h-3.5 w-3.5" strokeWidth={2.5} />
            Stop processing
          </Button>
        </>
      )}

      {startMutation.data && !startMutation.data.started && (
        <span className="rounded-lg border border-warning-border bg-warning-bg px-3 py-1.5 text-sm text-warning-fg">
          {startMutation.data.reason ?? "Couldn't start a new run"}
        </span>
      )}
    </div>
  );
}
