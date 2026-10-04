import { Loader2 } from "lucide-react";
import { cn } from "@/lib/utils";

interface LoadingStateProps {
  title?: string;
  description?: string;
  className?: string;
}

export function LoadingState({
  title = "Loading data...",
  description = "Please wait while we retrieve the latest information.",
  className,
}: LoadingStateProps) {
  return (
    <div
      role="status"
      aria-live="polite"
      className={cn(
        "flex min-h-[220px] flex-col items-center justify-center rounded-xl border border-border/80 bg-surface p-8 text-center",
        className
      )}
    >
      <Loader2 className="h-8 w-8 animate-spin text-teal" aria-hidden="true" />
      <h4 className="mt-4 text-sm font-semibold text-ink">{title}</h4>
      {description && <p className="mt-1 text-xs text-slate max-w-sm">{description}</p>}
    </div>
  );
}
