import { Loader2 } from "lucide-react";
import { cn } from "@/lib/utils";

interface ProcessingStateProps {
  title: string;
  stage: string;
  progressPercent?: number;
  description?: string;
  className?: string;
}

export function ProcessingState({
  title,
  stage,
  progressPercent,
  description,
  className,
}: ProcessingStateProps) {
  return (
    <div
      role="status"
      aria-live="polite"
      className={cn(
        "flex min-h-[220px] flex-col items-center justify-center rounded-xl border border-border bg-surface p-8 text-center",
        className
      )}
    >
      <Loader2 className="h-8 w-8 animate-spin text-teal" aria-hidden="true" />
      <h4 className="mt-4 text-sm font-semibold text-ink">{title}</h4>
      <div className="mt-2 inline-flex items-center gap-2 rounded-full bg-teal-soft px-3 py-1 text-xs font-medium text-teal">
        <span className="h-1.5 w-1.5 animate-ping rounded-full bg-teal" />
        {stage}
      </div>
      {typeof progressPercent === "number" && (
        <div className="mt-4 w-48 overflow-hidden rounded-full bg-cloud-subtle h-2">
          <div
            className="h-full bg-teal transition-all duration-300 rounded-full"
            style={{ width: `${Math.min(100, Math.max(0, progressPercent))}%` }}
          />
        </div>
      )}
      {description && <p className="mt-2 text-xs text-slate max-w-sm">{description}</p>}
    </div>
  );
}
