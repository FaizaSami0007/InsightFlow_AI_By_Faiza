"use client";

import React, { useState } from "react";
import { VisualizationSpec } from "@/types";

interface ScatterChartProps {
  spec: VisualizationSpec;
  data: Record<string, unknown>[];
}

export function ScatterChart({ spec, data }: ScatterChartProps) {
  const [hoveredIdx, setHoveredIdx] = useState<number | null>(null);

  if (!data || data.length === 0) {
    return <div className="p-8 text-center text-sm text-slate">No data available to plot scatter chart.</div>;
  }

  const xKey = (spec.x_axis as string) || Object.keys(data[0])[0];
  const yKey = typeof spec.y_axis === "string" ? spec.y_axis : Object.keys(data[0])[1];

  const points = data.map((d) => ({
    x: Number(d[xKey] ?? 0),
    y: Number(d[yKey] ?? 0),
  }));

  const maxX = Math.max(...points.map((p) => p.x), 1);
  const minX = Math.min(...points.map((p) => p.x), 0);
  const rangeX = maxX - minX || 1;

  const maxY = Math.max(...points.map((p) => p.y), 1);
  const minY = Math.min(...points.map((p) => p.y), 0);
  const rangeY = maxY - minY || 1;

  const svgWidth = 420;
  const svgHeight = 220;
  const chartWidth = 320;
  const chartHeight = 150;
  const paddingX = 60;
  const paddingY = 25;

  return (
    <div className="w-full overflow-x-auto py-2">
      <div className="relative min-w-[380px] flex justify-center">
        <svg viewBox={`0 0 ${svgWidth} ${svgHeight}`} className="w-full h-auto max-h-[260px] select-none">
          {/* Grid lines */}
          <line x1={paddingX} y1={paddingY} x2={paddingX + chartWidth} y2={paddingY} stroke="#E3E8EF" strokeDasharray="3 3" />
          <line x1={paddingX} y1={paddingY + chartHeight / 2} x2={paddingX + chartWidth} y2={paddingY + chartHeight / 2} stroke="#E3E8EF" strokeDasharray="3 3" />
          <line x1={paddingX} y1={paddingY + chartHeight} x2={paddingX + chartWidth} y2={paddingY + chartHeight} stroke="#172033" strokeWidth="1" />
          <line x1={paddingX} y1={paddingY} x2={paddingX} y2={paddingY + chartHeight} stroke="#172033" strokeWidth="1" />

          {/* Points */}
          {points.map((pt, idx) => {
            const cx = paddingX + ((pt.x - minX) / rangeX) * chartWidth;
            const cy = paddingY + chartHeight - ((pt.y - minY) / rangeY) * chartHeight;
            const isHovered = hoveredIdx === idx;

            return (
              <circle
                key={idx}
                cx={cx}
                cy={cy}
                r={isHovered ? 6 : 4}
                fill={isHovered ? "#2563EB" : "#0F766E"}
                opacity={isHovered ? 1 : 0.8}
                stroke="#FFFFFF"
                strokeWidth={isHovered ? 2 : 1}
                className="cursor-pointer transition-all duration-200"
                onMouseEnter={() => setHoveredIdx(idx)}
                onMouseLeave={() => setHoveredIdx(null)}
              />
            );
          })}

          {/* Axes labels */}
          <text
            x={paddingX + chartWidth / 2}
            y={paddingY + chartHeight + 28}
            textAnchor="middle"
            className="text-[10px] fill-slate font-semibold"
          >
            {xKey.replace(/_/g, " ").toUpperCase()}
          </text>
        </svg>

        {hoveredIdx !== null && (
          <div className="absolute top-0 right-4 bg-ink text-surface text-[11px] px-2.5 py-1 rounded shadow-md pointer-events-none">
            <span>{xKey}: </span>
            <span className="font-mono">{points[hoveredIdx].x.toLocaleString()}</span>
            <span className="mx-1">•</span>
            <span>{yKey}: </span>
            <span className="font-mono">{points[hoveredIdx].y.toLocaleString()}</span>
          </div>
        )}
      </div>
    </div>
  );
}
