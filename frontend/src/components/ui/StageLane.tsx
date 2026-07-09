import { Check } from "lucide-react";
import { LANES, type Lane } from "../../ws/stageTaxonomy";
import type { AgentUpdate } from "../../api/types";
import { cn } from "../../lib/utils";

export function StageLane({ lane, update }: { lane: Lane; update: AgentUpdate | undefined }) {
  const { label, stages } = LANES[lane];
  const progress = update?.progress ?? 0;
  const failed = update?.status === "failed";
  const done = update?.status === "completed";
  const currentIndex = update ? stages.findIndex((s) => s.key === update.stage) : -1;

  return (
    <div className="rounded-xl border border-neutral-border bg-surface p-4 shadow-soft">
      <div className="flex items-center justify-between">
        <h3 className="font-display text-sm font-semibold text-ink">{label}</h3>
        <span className={cn("font-mono text-xs tabular-nums", failed ? "text-danger-fg" : "text-muted")}>
          {progress.toFixed(0)}%
        </span>
      </div>

      {/* signal rail */}
      <ol className="relative mt-4 flex flex-col gap-0">
        {stages.map((stage, i) => {
          const reached = currentIndex >= 0 && i <= currentIndex;
          const isCurrent = i === currentIndex;
          const isLast = i === stages.length - 1;
          const stageFailed = isCurrent && failed;
          const stageLive = isCurrent && !failed && !done;

          return (
            <li key={stage.key} className="relative flex gap-3 pb-3 last:pb-0">
              {!isLast && (
                <span
                  aria-hidden
                  className={cn(
                    "absolute left-[7px] top-4 h-full w-px",
                    reached && !stageFailed ? "bg-brand" : "bg-neutral-border"
                  )}
                />
              )}

              <span className="relative z-10 mt-0.5 flex h-3.5 w-3.5 shrink-0 items-center justify-center">
                {stageLive && (
                  <span className="absolute inline-flex h-3.5 w-3.5 animate-rail-ping rounded-full bg-brand" />
                )}
                <span
                  className={cn(
                    "relative flex h-3.5 w-3.5 items-center justify-center rounded-full border",
                    stageFailed
                      ? "border-danger-fg bg-danger-fg"
                      : reached
                      ? "border-brand bg-brand"
                      : "border-neutral-border bg-surface"
                  )}
                >
                  {reached && !stageFailed && <Check className="h-2.5 w-2.5 text-white" strokeWidth={3} />}
                </span>
              </span>

              <span
                className={cn(
                  "text-xs leading-4",
                  stageFailed
                    ? "font-semibold text-danger-fg"
                    : isCurrent
                    ? "font-semibold text-ink"
                    : reached
                    ? "text-ink"
                    : "text-muted"
                )}
              >
                {stage.label}
              </span>
            </li>
          );
        })}
      </ol>

      {update && (
        <p className={cn("mt-3 border-t border-neutral-border pt-3 text-xs", failed ? "text-danger-fg" : "text-muted")}>
          {failed ? update.error ?? "Failed" : update.message}
        </p>
      )}
    </div>
  );
}
