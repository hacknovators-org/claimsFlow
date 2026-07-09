import type { Tone } from "../../theme/tokens";
import { MetricCard } from "./MetricCard";
import { StatusPill } from "./StatusPill";

interface StatItem {
  label: string;
  value: string | number;
  tone?: Tone;
}

export function StatRow({ items }: { items: StatItem[] }) {
  return (
    <div className="flex flex-wrap gap-3">
      {items.map((item) =>
        item.tone ? (
          <div key={item.label} className="flex flex-col gap-1.5 rounded-xl border border-neutral-border bg-surface px-4 py-3 shadow-soft">
            <span className="text-xs font-semibold uppercase tracking-wide text-muted">{item.label}</span>
            <StatusPill label={String(item.value)} tone={item.tone} />
          </div>
        ) : (
          <MetricCard key={item.label} label={item.label} value={item.value} />
        )
      )}
    </div>
  );
}
