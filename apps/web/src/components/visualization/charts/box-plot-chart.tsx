"use client";

import React from "react";
import { VisualizationSpec } from "@/types";

interface BoxPlotChartProps {
  spec: VisualizationSpec;
  data?: Record<string, unknown>[];
}

export function BoxPlotChart({ spec, data }: BoxPlotChartProps) {
  const opts = spec.options || {};
  const min = (opts.min as number) ?? 0;
  const q1 = (opts.q1 as number) ?? 25;
  const median = (opts.median as number) ?? 50;
  const q3 = (opts.q3 as number) ?? 75;
  const max = (opts.max as number) ?? 100;
  const mean = opts.mean as number | undefined;

  const range = max - min || 1;
  const svgWidth = 400;
  const svgHeight = 160;
  const paddingX = 60;
  const chartWidth = svgWidth - paddingX * 2;
  const centerY = 70;
  const boxHeight = 50;

  const getX = (val: number) => paddingX + ((val - min) / range) * chartWidth;

  const xMin = getX(min);
  const xQ1 = getX(q1);
  const xMed = getX(median);
  const xQ3 = getX(q3);
  const xMax = getX(max);

  return (
    <div className="w-full flex flex-col items-center py-4 px-2 select-none">
      <svg viewBox={`0 0 ${svgWidth} ${svgHeight}`} className="w-full max-w-[440px] h-auto">
        {/* Whiskers horizontal line */}
        <line x1={xMin} y1={centerY} x2={xQ1} y2={centerY} stroke="#172033" strokeWidth="2" />
        <line x1={xQ3} y1={centerY} x2={xMax} y2={centerY} stroke="#172033" strokeWidth="2" />

        {/* Min & Max End Caps */}
        <line x1={xMin} y1={centerY - 15} x2={xMin} y2={centerY + 15} stroke="#172033" strokeWidth="2" />
        <line x1={xMax} y1={centerY - 15} x2={xMax} y2={centerY + 15} stroke="#172033" strokeWidth="2" />

        {/* IQR Box */}
        <rect
          x={xQ1}
          y={centerY - boxHeight / 2}
          width={Math.max(xQ3 - xQ1, 2)}
          height={boxHeight}
          fill="#E6F4F1"
          stroke="#0F766E"
          strokeWidth="2"
          rx="3"
        />

        {/* Median Line */}
        <line
          x1={xMed}
          y1={centerY - boxHeight / 2}
          x2={xMed}
          y2={centerY + boxHeight / 2}
          stroke="#0F766E"
          strokeWidth="3"
        />

        {/* Value Labels */}
        <text x={xMin} y={centerY + 32} textAnchor="middle" className="text-[10px] fill-slate font-mono">
          Min: {min.toLocaleString()}
        </text>
        <text x={xQ1} y={centerY - 32} textAnchor="middle" className="text-[10px] fill-slate font-mono">
          Q1: {q1.toLocaleString()}
        </text>
        <text x={xMed} y={centerY + 32} textAnchor="middle" className="text-[10px] fill-teal font-bold font-mono">
          Med: {median.toLocaleString()}
        </text>
        <text x={xQ3} y={centerY - 32} textAnchor="middle" className="text-[10px] fill-slate font-mono">
          Q3: {q3.toLocaleString()}
        </text>
        <text x={xMax} y={centerY + 32} textAnchor="middle" className="text-[10px] fill-slate font-mono">
          Max: {max.toLocaleString()}
        </text>
      </svg>
    </div>
  );
}
