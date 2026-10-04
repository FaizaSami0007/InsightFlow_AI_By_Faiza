import * as React from "react";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/lib/utils";

const badgeVariants = cva(
  "inline-flex items-center gap-1 rounded-full px-2.5 py-0.5 text-xs font-medium transition-colors select-none",
  {
    variants: {
      variant: {
        default: "bg-cloud text-ink border border-border",
        teal: "bg-teal-soft text-teal border border-teal-border",
        blue: "bg-blue-soft text-blue border border-blue-border",
        amber: "bg-amber-soft text-amber border border-amber-border",
        danger: "bg-danger-soft text-danger border border-danger-border",
        outline: "border border-border text-slate",
      },
    },
    defaultVariants: {
      variant: "default",
    },
  }
);

export interface BadgeProps
  extends React.HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof badgeVariants> {
  dot?: boolean;
}

export function Badge({ className, variant, dot, children, ...props }: BadgeProps) {
  return (
    <div className={cn(badgeVariants({ variant }), className)} {...props}>
      {dot && (
        <span
          className={cn(
            "h-1.5 w-1.5 rounded-full",
            variant === "teal" && "bg-teal",
            variant === "blue" && "bg-blue",
            variant === "amber" && "bg-amber",
            variant === "danger" && "bg-danger",
            (!variant || variant === "default" || variant === "outline") && "bg-slate"
          )}
          aria-hidden="true"
        />
      )}
      {children}
    </div>
  );
}
