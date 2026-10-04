"use client";

import React from "react";
import { VisualizationSpec } from "@/types";
import { Activity } from "lucide-react";

interface KpiCardProps {
  spec: VisualizationSpec;
  data?: Record<string, unknown>[];
}

export function KpiCard({ spec, data }: KpiCardProps) {
  let displayValue: string | number = "—";
  let label = spec.options?.kpi_label as string | undefined;

  if (spec.options?.kpi_value !== undefined && spec.options?.kpi_value !== null) {
    displayValue = spec.options.kpi_value as number | string;
  } else if (data && data.length > 0) {
    const firstRow = data[0];
    const metricKey = typeof spec.y_axis === "string" ? spec.y_axis : Object.keys(firstRow)[0];
    displayValue = firstRow[metricKey] as number | string;
    if (!label) label = metricKey.replace(/_/g, " ");
  }

  // Format number
  let formattedValue = displayValue;
  if (typeof displayValue === "number") {
    if (Math.abs(displayValue) >= 1_000_000) {
      formattedValue = `${(displayValue / 1_000_000).toFixed(2)}M`;
    } else if (Math.abs(displayValue) >= 1_000) {
      formattedValue = `${(displayValue / 1_000).toFixed(2)}K`;
    } else {
      formattedValue = displayValue.toLocaleString(undefined, { maximumFractionDigits: 2 });
    }
  }

  return (
    <div className="flex flex-col items-center justify-center p-8 bg-surface border border-border rounded-xl shadow-sm text-center">
      <div className="flex items-center gap-2 mb-2 text-xs font-semibold uppercase tracking-wider text-slate">
        <Activity className="w-4 h-4 text-teal" />
        <span>{label || spec.title}</span>
      </div>
      <div className="text-4xl sm:text-5xl font-extrabold text-ink tracking-tight my-2">
        {formattedValue}
      </div>
      {spec.subtitle && (
        <p className="text-xs text-slate mt-2 max-w-sm">{spec.subtitle}</p>
      )}
    </div>
  );
}
