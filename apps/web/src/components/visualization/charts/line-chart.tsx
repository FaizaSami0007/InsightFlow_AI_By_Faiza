"use client";

import React, { useState } from "react";
import { VisualizationSpec } from "@/types";

interface LineChartProps {
  spec: VisualizationSpec;
  data: Record<string, unknown>[];
  isArea?: boolean;
}

export function LineChart({ spec, data, isArea = false }: LineChartProps) {
  const [hoveredIdx, setHoveredIdx] = useState<number | null>(null);

  if (!data || data.length === 0) {
    return <div className="p-8 text-center text-sm text-slate">No data available to plot line chart.</div>;
  }

  const xKey = (spec.x_axis as string) || Object.keys(data[0])[0];
  const yKey = typeof spec.y_axis === "string" ? spec.y_axis : Object.keys(data[0])[1];

  const points = data.map((d) => ({
    xLabel: String(d[xKey] ?? ""),
    yVal: Number(d[yKey] ?? 0),
  }));

  const maxVal = Math.max(...points.map((p) => p.yVal), 1);
  const minVal = Math.min(...points.map((p) => p.yVal), 0);
  const range = maxVal - minVal || 1;

  const svgWidth = Math.max(points.length * 60 + 80, 420);
  const svgHeight = 220;
  const chartHeight = 150;
  const paddingX = 50;
  const paddingY = 25;

  const coords = points.map((p, idx) => {
    const x = paddingX + idx * ((svgWidth - paddingX * 2) / Math.max(points.length - 1, 1));
    const y = paddingY + chartHeight - ((p.yVal - minVal) / range) * chartHeight;
    return { ...p, x, y };
  });

  const pathD = coords.reduce((acc, curr, idx) => {
    return idx === 0 ? `M ${curr.x},${curr.y}` : `${acc} L ${curr.x},${curr.y}`;
  }, "");

  const areaD = `${pathD} L ${coords[coords.length - 1].x},${paddingY + chartHeight} L ${coords[0].x},${
    paddingY + chartHeight
  } Z`;

  return (
    <div className="w-full overflow-x-auto py-2">
      <div className="relative min-w-[380px] flex justify-center">
        <svg viewBox={`0 0 ${svgWidth} ${svgHeight}`} className="w-full h-auto max-h-[260px] select-none">
          <defs>
            <linearGradient id="areaGradient" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#0F766E" stopOpacity="0.3" />
              <stop offset="100%" stopColor="#0F766E" stopOpacity="0.0" />
            </linearGradient>
          </defs>

          {/* Grid lines */}
          <line x1={paddingX} y1={paddingY} x2={svgWidth - paddingX} y2={paddingY} stroke="#E3E8EF" strokeDasharray="3 3" />
          <line x1={paddingX} y1={paddingY + chartHeight / 2} x2={svgWidth - paddingX} y2={paddingY + chartHeight / 2} stroke="#E3E8EF" strokeDasharray="3 3" />
          <line x1={paddingX} y1={paddingY + chartHeight} x2={svgWidth - paddingX} y2={paddingY + chartHeight} stroke="#172033" strokeWidth="1" />

          {/* Area fill */}
          {(isArea || spec.chart_type === "area") && (
            <path d={areaD} fill="url(#areaGradient)" />
          )}

          {/* Line stroke */}
          <path d={pathD} fill="none" stroke="#0F766E" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round" />

          {/* Interactive points */}
          {coords.map((pt, idx) => {
            const isHovered = hoveredIdx === idx;
            return (
              <g
                key={idx}
                onMouseEnter={() => setHoveredIdx(idx)}
                onMouseLeave={() => setHoveredIdx(null)}
                className="cursor-pointer"
              >
                <circle
                  cx={pt.x}
                  cy={pt.y}
                  r={isHovered ? 6 : 4}
                  fill="#FFFFFF"
                  stroke="#0F766E"
                  strokeWidth={isHovered ? 3 : 2}
                  className="transition-all duration-200"
                />
                {/* X axis tick label */}
                <text
                  x={pt.x}
                  y={paddingY + chartHeight + 16}
                  textAnchor="middle"
                  className="text-[10px] fill-slate font-medium"
                >
                  {pt.xLabel.length > 8 ? `${pt.xLabel.slice(0, 7)}…` : pt.xLabel}
                </text>
              </g>
            );
          })}
        </svg>

        {hoveredIdx !== null && (
          <div className="absolute top-0 right-4 bg-ink text-surface text-[11px] px-2.5 py-1 rounded shadow-md pointer-events-none">
            <span className="font-semibold">{coords[hoveredIdx].xLabel}:</span>{" "}
            <span className="font-mono">{coords[hoveredIdx].yVal.toLocaleString()}</span>
          </div>
        )}
      </div>
    </div>
  );
}
