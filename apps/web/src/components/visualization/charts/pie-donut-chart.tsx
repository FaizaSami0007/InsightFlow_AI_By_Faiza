"use client";

import React, { useState } from "react";
import { VisualizationSpec } from "@/types";

interface PieDonutChartProps {
  spec: VisualizationSpec;
  data: Record<string, unknown>[];
  isDonut?: boolean;
}

const PALETTE = ["#0F766E", "#2563EB", "#D97706", "#059669", "#7C3AED", "#DB2777"];

export function PieDonutChart({ spec, data, isDonut = true }: PieDonutChartProps) {
  const [hoveredIdx, setHoveredIdx] = useState<number | null>(null);

  if (!data || data.length === 0) {
    return <div className="p-8 text-center text-sm text-slate">No data available to plot pie/donut chart.</div>;
  }

  const catKey = (spec.x_axis as string) || Object.keys(data[0])[0];
  const valKey = (spec.y_axis as string) || Object.keys(data[0])[1];

  const items = data.map((d) => ({
    label: String(d[catKey] ?? "Unknown"),
    value: Math.max(Number(d[valKey] ?? 0), 0),
  }));

  const total = items.reduce((acc, curr) => acc + curr.value, 0) || 1;

  // Compute SVG arc angles
  const size = 200;
  const center = size / 2;
  const radius = 80;
  const innerRadius = isDonut ? 50 : 0;

  let startAngle = 0;
  const arcs = items.map((item, idx) => {
    const angle = (item.value / total) * 2 * Math.PI;
    const endAngle = startAngle + angle;
    const color = PALETTE[idx % PALETTE.length];

    // Calculate arc coordinates
    const x1 = center + radius * Math.cos(startAngle - Math.PI / 2);
    const y1 = center + radius * Math.sin(startAngle - Math.PI / 2);
    const x2 = center + radius * Math.cos(endAngle - Math.PI / 2);
    const y2 = center + radius * Math.sin(endAngle - Math.PI / 2);

    const x3 = center + innerRadius * Math.cos(endAngle - Math.PI / 2);
    const y3 = center + innerRadius * Math.sin(endAngle - Math.PI / 2);
    const x4 = center + innerRadius * Math.cos(startAngle - Math.PI / 2);
    const y4 = center + innerRadius * Math.sin(startAngle - Math.PI / 2);

    const largeArc = angle > Math.PI ? 1 : 0;

    let pathD = "";
    if (isDonut) {
      pathD = `M ${x1},${y1} A ${radius},${radius} 0 ${largeArc} 1 ${x2},${y2} L ${x3},${y3} A ${innerRadius},${innerRadius} 0 ${largeArc} 0 ${x4},${y4} Z`;
    } else {
      pathD = `M ${center},${center} L ${x1},${y1} A ${radius},${radius} 0 ${largeArc} 1 ${x2},${y2} Z`;
    }

    const currentStart = startAngle;
    startAngle = endAngle;

    return {
      ...item,
      color,
      pathD,
      percentage: ((item.value / total) * 100).toFixed(1),
      startAngle: currentStart,
      endAngle,
    };
  });

  return (
    <div className="flex flex-col sm:flex-row items-center justify-center gap-6 py-4 px-2">
      {/* SVG Donut / Pie */}
      <div className="relative">
        <svg viewBox={`0 0 ${size} ${size}`} className="w-48 h-48 select-none">
          {arcs.map((arc, idx) => {
            const isHovered = hoveredIdx === idx;
            return (
              <path
                key={idx}
                d={arc.pathD}
                fill={arc.color}
                stroke="#FFFFFF"
                strokeWidth="2"
                className={`transition-all duration-200 cursor-pointer ${
                  isHovered ? "opacity-100 scale-105 origin-center filter drop-shadow-md" : "opacity-90"
                }`}
                onMouseEnter={() => setHoveredIdx(idx)}
                onMouseLeave={() => setHoveredIdx(null)}
              />
            );
          })}
        </svg>

        {isDonut && (
          <div className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none text-center">
            <span className="text-[10px] uppercase font-bold text-slate">Total</span>
            <span className="text-xs font-mono font-extrabold text-ink">
              {total >= 1000 ? `${(total / 1000).toFixed(1)}k` : total.toLocaleString()}
            </span>
          </div>
        )}
      </div>

      {/* Legend List */}
      <div className="flex flex-col gap-2 max-w-[200px] text-xs">
        {arcs.map((arc, idx) => {
          const isHovered = hoveredIdx === idx;
          return (
            <div
              key={idx}
              className={`flex items-center gap-2 p-1.5 rounded-md cursor-pointer transition-colors ${
                isHovered ? "bg-cloud font-semibold text-ink" : "text-slate"
              }`}
              onMouseEnter={() => setHoveredIdx(idx)}
              onMouseLeave={() => setHoveredIdx(null)}
            >
              <span className="w-3 h-3 rounded-full flex-shrink-0" style={{ backgroundColor: arc.color }} />
              <span className="truncate" title={arc.label}>
                {arc.label}
              </span>
              <span className="ml-auto font-mono text-teal font-bold">{arc.percentage}%</span>
            </div>
          );
        })}
      </div>
    </div>
  );
}
