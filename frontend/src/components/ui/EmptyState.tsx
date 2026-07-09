import type { ReactNode } from "react";
import { Inbox } from "lucide-react";

export function EmptyState({ message, icon }: { message: string; icon?: ReactNode }) {
  return (
    <div className="flex flex-col items-center justify-center gap-3 rounded-xl border border-dashed border-neutral-border bg-canvas/50 px-6 py-14 text-center">
      <div className="flex h-11 w-11 items-center justify-center rounded-full bg-brand-light text-brand">
        {icon ?? <Inbox className="h-5 w-5" strokeWidth={1.75} />}
      </div>
      <p className="max-w-sm text-sm text-muted">{message}</p>
    </div>
  );
}
