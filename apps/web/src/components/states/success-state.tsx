import * as React from "react";
import { CheckCircle2 } from "lucide-react";
import { cn } from "@/lib/utils";

interface SuccessStateProps {
  title: string;
  message: string;
  action?: React.ReactNode;
  className?: string;
}

export function SuccessState({ title, message, action, className }: SuccessStateProps) {
  return (
    <div
      className={cn(
        "flex min-h-[220px] flex-col items-center justify-center rounded-xl border border-teal-border bg-teal-soft/30 p-8 text-center",
        className
      )}
    >
      <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-teal-soft text-teal">
        <CheckCircle2 className="h-6 w-6" aria-hidden="true" />
      </div>
      <h4 className="mt-4 text-sm font-semibold text-ink">{title}</h4>
      <p className="mt-1.5 max-w-md text-xs text-slate leading-relaxed">{message}</p>
      {action && <div className="mt-4">{action}</div>}
    </div>
  );
}
