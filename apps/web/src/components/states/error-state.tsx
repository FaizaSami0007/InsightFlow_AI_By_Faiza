import * as React from "react";
import { AlertCircle, RotateCcw } from "lucide-react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

interface ErrorStateProps {
  title?: string;
  message: string;
  onRetry?: () => void;
  className?: string;
}

export function ErrorState({
  title = "Failed to load data",
  message,
  onRetry,
  className,
}: ErrorStateProps) {
  return (
    <div
      role="alert"
      className={cn(
        "flex min-h-[220px] flex-col items-center justify-center rounded-xl border border-danger/30 bg-danger-soft/20 p-8 text-center",
        className
      )}
    >
      <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-danger-soft text-danger">
        <AlertCircle className="h-6 w-6" aria-hidden="true" />
      </div>
      <h4 className="mt-4 text-sm font-semibold text-danger">{title}</h4>
      <p className="mt-1.5 max-w-md text-xs text-slate leading-relaxed">{message}</p>
      {onRetry && (
        <Button
          variant="outline"
          size="sm"
          onClick={onRetry}
          leftIcon={<RotateCcw className="h-3.5 w-3.5" />}
          className="mt-4 border-danger/30 text-danger hover:bg-danger-soft"
        >
          Try Again
        </Button>
      )}
    </div>
  );
}
