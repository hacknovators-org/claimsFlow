export function MetricCard({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="flex-1 rounded-xl border border-neutral-border bg-surface px-4 py-3 shadow-soft">
      <div className="text-xs font-semibold uppercase tracking-wide text-muted">{label}</div>
      <div className="mt-1 font-display text-2xl font-semibold text-ink">{value}</div>
    </div>
  );
}
