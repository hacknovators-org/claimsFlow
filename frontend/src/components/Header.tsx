import { NavLink } from "react-router-dom";
import { Workflow } from "lucide-react";
import type { ConnectionState } from "../ws/useWebSocket";
import { StatusPill } from "./ui/StatusPill";
import { cn } from "../lib/utils";

const CONNECTION_LABEL: Record<ConnectionState, string> = {
  connecting: "Connecting",
  open: "Live",
  reconnecting: "Reconnecting",
  closed: "Disconnected",
};

const CONNECTION_TONE: Record<ConnectionState, "success" | "warning" | "danger" | "neutral"> = {
  connecting: "neutral",
  open: "success",
  reconnecting: "warning",
  closed: "danger",
};

const NAV_LINKS = [
  { to: "/", label: "Dashboard" },
  { to: "/history", label: "History" },
];

export function Header({ connectionState }: { connectionState: ConnectionState }) {
  return (
    <header className="flex items-center justify-between border-b border-console-border bg-console px-6 py-3.5">
      <div className="flex items-center gap-8">
        <span className="flex items-center gap-2 font-display text-lg font-semibold tracking-tight text-console-fg">
          <Workflow className="h-5 w-5 text-brand" strokeWidth={2} />
          Claims Flow
        </span>
        <nav className="flex items-center gap-1 text-sm font-medium">
          {NAV_LINKS.map((link) => (
            <NavLink
              key={link.to}
              to={link.to}
              end={link.to === "/"}
              className={({ isActive }) =>
                cn(
                  "rounded-md px-3 py-1.5 transition-colors",
                  isActive ? "bg-console-raised text-console-fg" : "text-console-muted hover:text-console-fg"
                )
              }
            >
              {link.label}
            </NavLink>
          ))}
        </nav>
      </div>
      <StatusPill label={CONNECTION_LABEL[connectionState]} tone={CONNECTION_TONE[connectionState]} />
    </header>
  );
}
