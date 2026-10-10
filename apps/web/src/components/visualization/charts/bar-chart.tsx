"use client";

import React, { useState } from "react";
import { VisualizationSpec } from "@/types";

interface BarChartProps {
  spec: VisualizationSpec;
  data: Record<string, unknown>[];
  horizontal?: boolean;
}

export function BarChart({ spec, data, horizontal = false }: BarChartProps) {
  const [hoveredIdx, setHoveredIdx] = useState<number | null>(null);

  if (!data || data.length === 0) {
    return <div className="p-8 text-center text-sm text-slate">No data available to plot bar chart.</div>;
  }

  const isHorizontal = horizontal || spec.chart_type === "horizontal_bar";
  const catKey = isHorizontal ? (spec.y_axis as string) : (spec.x_axis as string);
  const valKey = isHorizontal ? (spec.x_axis as string) : (spec.y_axis as string);

  // Extract labels and numbers
  const items = data.map((d) => ({
    label: String(d[catKey] ?? "Unknown"),
    value: Number(d[valKey] ?? 0),
  }));

  const maxVal = Math.max(...items.map((it) => it.value), 1);

  if (isHorizontal) {
    return (
      <div className="w-full py-4 px-2 flex flex-col gap-3">
        {items.map((item, idx) => {
          const pct = Math.max((item.value / maxVal) * 100, 2);
          const isHovered = hoveredIdx === idx;
          return (
            <div
              key={idx}
              className="flex flex-col gap-1 text-xs"
              onMouseEnter={() => setHoveredIdx(idx)}
              onMouseLeave={() => setHoveredIdx(null)}
            >
              <div className="flex items-center justify-between text-slate font-medium">
                <span className="truncate max-w-[200px] text-ink font-semibold" title={item.label}>
                  {item.label}
                </span>
                <span className="font-mono text-teal font-bold">
                  {item.value.toLocaleString(undefined, { maximumFractionDigits: 2 })}
                </span>
              </div>
              <div className="w-full bg-cloud h-6 rounded-md overflow-hidden p-0.5 border border-border flex items-center">
                <div
                  className={`h-full rounded transition-all duration-300 ${
                    isHovered ? "bg-teal shadow-md" : "bg-teal/80"
                  }`}
                  style={{ width: `${pct}%` }}
                />
              </div>
            </div>
          );
        })}
      </div>
    );
  }

  // Vertical Bar Chart
  const svgHeight = 220;
  const svgWidth = Math.max(items.length * 60 + 80, 400);
  const chartHeight = 160;
  const barWidth = Math.min(Math.max(300 / items.length, 24), 48);

  return (
    <div className="w-full overflow-x-auto py-2">
      <div className="relative w-full min-w-0 flex justify-center">
        <svg
          viewBox={`0 0 ${svgWidth} ${svgHeight}`}
          className="w-full h-auto max-h-[260px] select-none"
        >
          {/* Grid lines */}
          <line x1="40" y1="20" x2={svgWidth - 20} y2="20" stroke="#E3E8EF" strokeDasharray="3 3" />
          <line x1="40" y1={20 + chartHeight / 2} x2={svgWidth - 20} y2={20 + chartHeight / 2} stroke="#E3E8EF" strokeDasharray="3 3" />
          <line x1="40" y1={20 + chartHeight} x2={svgWidth - 20} y2={20 + chartHeight} stroke="#172033" strokeWidth="1" />

          {/* Bars */}
          {items.map((item, idx) => {
            const barHeight = Math.max((item.value / maxVal) * chartHeight, 4);
            const xPos = 60 + idx * ((svgWidth - 80) / Math.max(items.length, 1));
            const yPos = 20 + chartHeight - barHeight;
            const isHovered = hoveredIdx === idx;
            const maxLabelLen = items.length <= 2 ? 18 : items.length <= 5 ? 12 : 8;
            const displayLabel = item.label.length > maxLabelLen ? `${item.label.slice(0, maxLabelLen - 1)}…` : item.label;

            return (
              <g
                key={idx}
                onMouseEnter={() => setHoveredIdx(idx)}
                onMouseLeave={() => setHoveredIdx(null)}
                className="cursor-pointer group"
              >
                <rect
                  x={xPos - barWidth / 2}
                  y={yPos}
                  width={barWidth}
                  height={barHeight}
                  rx="4"
                  fill={isHovered ? "#0F766E" : "#14B8A6"}
                  className="transition-all duration-200"
                />
                {/* Value on top */}
                <text
                  x={xPos}
                  y={yPos - 6}
                  textAnchor="middle"
                  className={`text-[10px] font-mono font-semibold transition-opacity duration-200 ${
                    isHovered ? "fill-ink opacity-100" : "fill-slate opacity-80"
                  }`}
                >
                  {item.value >= 1000 ? `${(item.value / 1000).toFixed(1)}k` : item.value}
                </text>
                {/* Category Label at bottom */}
                <text
                  x={xPos}
                  y={20 + chartHeight + 16}
                  textAnchor="middle"
                  className="text-[11px] fill-slate font-medium"
                >
                  <title>{item.label}</title>
                  {displayLabel}
                </text>
              </g>
            );
          })}
        </svg>

        {hoveredIdx !== null && (
          <div className="absolute top-0 right-4 bg-ink text-surface text-[11px] px-2.5 py-1 rounded shadow-md pointer-events-none">
            <span className="font-semibold">{items[hoveredIdx].label}:</span>{" "}
            <span className="font-mono">{items[hoveredIdx].value.toLocaleString()}</span>
          </div>
        )}
      </div>
    </div>
  );
}
