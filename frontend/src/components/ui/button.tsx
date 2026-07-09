import { cn } from "../../lib/utils";

type Variant = "primary" | "danger" | "outline";

const VARIANT_CLASSES: Record<Variant, string> = {
  primary: "bg-brand text-white shadow-soft hover:bg-brand-dark disabled:bg-brand/40 disabled:shadow-none",
  danger: "bg-danger-fg text-white shadow-soft hover:bg-danger-fg/85 disabled:bg-danger-fg/40 disabled:shadow-none",
  outline: "border border-neutral-border bg-surface text-ink hover:border-ink/30 hover:bg-canvas disabled:text-muted",
};

interface ButtonProps extends React.ComponentProps<"button"> {
  variant?: Variant;
}

export function Button({ className, variant = "primary", ...props }: ButtonProps) {
  return (
    <button
      className={cn(
        "inline-flex items-center justify-center gap-2 rounded-lg px-4 py-2.5 text-sm font-semibold tracking-tight",
        "transition-colors duration-150 disabled:cursor-not-allowed",
        VARIANT_CLASSES[variant],
        className
      )}
      {...props}
    />
  );
}
