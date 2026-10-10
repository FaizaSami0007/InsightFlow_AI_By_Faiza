import * as React from "react";
import { cn } from "@/lib/utils";

export interface PageHeroMetric {
  label: string;
  value: React.ReactNode;
  unit?: string;
  description?: string;
  variant?: "teal" | "blue" | "amber" | "danger" | "default";
}

export interface PageHeroProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: "default" | "gradient";
  phaseBadge?: string;
  subtitle?: string;
  statusBadge?: React.ReactNode;
  icon?: React.ReactNode;
  title: string;
  description?: React.ReactNode;
  badge?: React.ReactNode;
  metric?: PageHeroMetric;
  actions?: React.ReactNode;
  iconVariant?: "teal" | "blue" | "amber" | "purple" | "danger" | "default";
}

export const PageHero = React.forwardRef<HTMLDivElement, PageHeroProps>(
  (
    {
      className,
      variant = "default",
      phaseBadge,
      subtitle,
      statusBadge,
      icon,
      title,
      description,
      badge,
      metric,
      actions,
      iconVariant = "teal",
      ...props
    },
    ref
  ) => {
    const iconColors: Record<string, string> = {
      teal: "bg-teal-soft text-teal border-teal-border",
      blue: "bg-blue-soft text-blue border-blue-border",
      amber: "bg-amber-soft text-amber border-amber-border",
      purple: "bg-purple-50 text-purple-700 border-purple-200",
      danger: "bg-danger-soft text-danger border-danger-border",
      default: "bg-cloud text-ink border-border",
    };

    const metricColors: Record<string, string> = {
      teal: "text-teal",
      blue: "text-blue",
      amber: "text-amber",
      danger: "text-danger",
      default: "text-ink",
    };

    if (variant === "gradient") {
      return (
        <div
          ref={ref}
          className={cn(
            "w-full rounded-2xl bg-gradient-to-r from-teal-900 via-teal-800 to-slate-900 text-white p-5 sm:p-6 shadow-soft-lg border border-teal-700/30 transition-all",
            className
          )}
          {...props}
        >
          <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4 min-w-0">
            {/* Left: Metadata, Title, Description */}
            <div className="min-w-0 flex-1">
              {(phaseBadge || subtitle) && (
                <div className="flex flex-wrap items-center gap-2 mb-1.5">
                  {phaseBadge && (
                    <span className="px-2.5 py-0.5 rounded-full bg-teal-500/20 text-teal-300 text-xs font-semibold uppercase tracking-wider border border-teal-400/30">
                      {phaseBadge}
                    </span>
                  )}
                  {subtitle && (
                    <span className="text-xs text-teal-200/80 font-medium">
                      {subtitle}
                    </span>
                  )}
                </div>
              )}

              <div className="flex items-center gap-2.5 flex-wrap">
                {icon && (
                  <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-white/10 border border-white/15 text-teal-300 shadow-soft">
                    {icon}
                  </div>
                )}
                <h1 className="text-xl sm:text-2xl font-bold tracking-tight text-white break-words">
                  {title}
                </h1>
                {badge}
              </div>

              {description && (
                <p className="text-xs sm:text-sm text-slate-300 max-w-2xl mt-1 leading-relaxed">
                  {description}
                </p>
              )}
            </div>

            {/* Right: Status badge, Metrics, Actions */}
            {(statusBadge || metric || actions) && (
              <div className="flex flex-wrap items-center gap-3 shrink-0">
                {statusBadge && (
                  <div className="flex items-center gap-2 px-3 py-1.5 rounded-xl bg-white/10 backdrop-blur border border-white/15 text-xs text-teal-100 whitespace-nowrap">
                    {statusBadge}
                  </div>
                )}

                {metric && (
                  <div className="text-left sm:text-right shrink-0 px-3.5 py-2 rounded-xl bg-white/10 backdrop-blur border border-white/15">
                    <span className="text-[10px] text-teal-200 block font-medium uppercase tracking-wider">
                      {metric.label}
                    </span>
                    <div className="flex items-baseline gap-1 sm:justify-end">
                      <span className="text-lg sm:text-xl font-bold font-mono tracking-tight text-white">
                        {metric.value}
                      </span>
                      {metric.unit && (
                        <span className="text-xs font-normal text-teal-200/80">
                          {metric.unit}
                        </span>
                      )}
                    </div>
                    {metric.description && (
                      <span className="text-[10px] text-slate-300 block">
                        {metric.description}
                      </span>
                    )}
                  </div>
                )}

                {actions && (
                  <div className="flex flex-wrap items-center gap-2">
                    {actions}
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      );
    }

    return (
      <div
        ref={ref}
        className={cn(
          "w-full rounded-2xl border border-border bg-surface p-4 sm:p-5 lg:p-6 text-ink shadow-soft transition-all",
          className
        )}
        {...props}
      >
        {/* Responsive Hero Container:
            - On XL screens (>=1280px): 1-row flex layout [Title/Description] ... [Metric] [Actions]
            - On LG/MD screens (768px-1279px): 2-row layout with Title full width on top, and Metric + Actions below
            - On Mobile (<768px): Clean stacked layout with fluid wrap
        */}
        <div className="flex flex-col gap-4 xl:flex-row xl:items-center xl:justify-between min-w-0">
          {/* Left: Icon + Title + Description */}
          <div className="flex items-start gap-3 sm:gap-3.5 min-w-0 flex-1">
            {icon && (
              <div
                className={cn(
                  "flex h-10 w-10 sm:h-11 sm:w-11 shrink-0 items-center justify-center rounded-xl border shadow-soft transition-transform",
                  iconColors[iconVariant] || iconColors.teal
                )}
                aria-hidden="true"
              >
                {icon}
              </div>
            )}
            <div className="space-y-0.5 min-w-0 flex-1">
              <div className="flex flex-wrap items-center gap-2">
                <h1 className="text-base sm:text-lg lg:text-xl font-bold tracking-tight text-ink break-words">
                  {title}
                </h1>
                {badge}
              </div>
              {description && (
                <p className="text-xs text-slate leading-relaxed break-words">
                  {description}
                </p>
              )}
            </div>
          </div>

          {/* Right / Bottom: Metric + Actions */}
          {(metric || actions) && (
            <div
              className={cn(
                "flex flex-wrap items-center gap-3 sm:gap-4 pt-3 xl:pt-0 border-t xl:border-t-0 border-border/70 min-w-0 w-full xl:w-auto",
                metric ? "justify-between xl:justify-end" : "justify-start xl:justify-end"
              )}
            >
              {metric && (
                <div className="text-left sm:text-right shrink-0 pr-1">
                  <span className="text-[10px] sm:text-[11px] text-slate block font-medium uppercase tracking-wider">
                    {metric.label}
                  </span>
                  <div className="flex items-baseline gap-1 sm:justify-end">
                    <span
                      className={cn(
                        "text-lg sm:text-xl font-bold font-mono tracking-tight",
                        metricColors[metric.variant || "teal"]
                      )}
                    >
                      {metric.value}
                    </span>
                    {metric.unit && (
                      <span className="text-xs font-normal text-slate">
                        {metric.unit}
                      </span>
                    )}
                  </div>
                  {metric.description && (
                    <span className="text-[10px] text-slate/70 block">
                      {metric.description}
                    </span>
                  )}
                </div>
              )}

              {actions && (
                <div className="flex flex-wrap items-center gap-2 sm:gap-2.5 min-w-0">
                  {actions}
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    );
  }
);

PageHero.displayName = "PageHero";
