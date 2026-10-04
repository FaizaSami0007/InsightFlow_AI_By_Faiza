"use client";

import React, { useState } from "react";
import { VisualizationSpec } from "@/types";

interface HistogramChartProps {
  spec: VisualizationSpec;
  data: Record<string, unknown>[];
}

export function HistogramChart({ spec, data }: HistogramChartProps) {
  const [hoveredIdx, setHoveredIdx] = useState<number | null>(null);

  if (!data || data.length === 0) {
    return <div className="p-8 text-center text-sm text-slate">No data available to plot histogram.</div>;
  }

  const xKey = (spec.x_axis as string) || Object.keys(data[0])[0];
  const yKey = (spec.y_axis as string) || Object.keys(data[0])[1];

  const bins = data.map((d) => ({
    rangeLabel: String(d[xKey] ?? ""),
    count: Number(d[yKey] ?? 0),
  }));

  const maxCount = Math.max(...bins.map((b) => b.count), 1);
  const svgWidth = Math.max(bins.length * 50 + 80, 400);
  const svgHeight = 220;
  const chartHeight = 150;
  const paddingX = 40;
  const paddingY = 25;
  const barWidth = (svgWidth - paddingX * 2) / Math.max(bins.length, 1);

  return (
    <div className="w-full overflow-x-auto py-2">
      <div className="relative min-w-[380px] flex justify-center">
        <svg viewBox={`0 0 ${svgWidth} ${svgHeight}`} className="w-full h-auto max-h-[260px] select-none">
          {/* Grid lines */}
          <line x1={paddingX} y1={paddingY} x2={svgWidth - paddingX} y2={paddingY} stroke="#E3E8EF" strokeDasharray="3 3" />
          <line x1={paddingX} y1={paddingY + chartHeight / 2} x2={svgWidth - paddingX} y2={paddingY + chartHeight / 2} stroke="#E3E8EF" strokeDasharray="3 3" />
          <line x1={paddingX} y1={paddingY + chartHeight} x2={svgWidth - paddingX} y2={paddingY + chartHeight} stroke="#172033" strokeWidth="1" />

          {/* Histogram Bins */}
          {bins.map((bin, idx) => {
            const h = (bin.count / maxCount) * chartHeight;
            const x = paddingX + idx * barWidth;
            const y = paddingY + chartHeight - h;
            const isHovered = hoveredIdx === idx;

            return (
              <g
                key={idx}
                onMouseEnter={() => setHoveredIdx(idx)}
                onMouseLeave={() => setHoveredIdx(null)}
                className="cursor-pointer"
              >
                <rect
                  x={x + 1}
                  y={y}
                  width={Math.max(barWidth - 2, 2)}
                  height={h}
                  fill={isHovered ? "#2563EB" : "#3B82F6"}
                  opacity={isHovered ? 1 : 0.85}
                  className="transition-all duration-200"
                />
                <text
                  x={x + barWidth / 2}
                  y={paddingY + chartHeight + 14}
                  textAnchor="middle"
                  className="text-[9px] fill-slate font-mono"
                >
                  {bin.rangeLabel.length > 7 ? `${bin.rangeLabel.slice(0, 6)}…` : bin.rangeLabel}
                </text>
              </g>
            );
          })}
        </svg>

        {hoveredIdx !== null && (
          <div className="absolute top-0 right-4 bg-ink text-surface text-[11px] px-2.5 py-1 rounded shadow-md pointer-events-none">
            <span>Range: {bins[hoveredIdx].rangeLabel}</span>
            <span className="mx-1">•</span>
            <span className="font-mono">Count: {bins[hoveredIdx].count.toLocaleString()}</span>
          </div>
        )}
      </div>
    </div>
  );
}
