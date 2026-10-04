"use client";

import React, { useState, useRef } from "react";
import { ChartType, VisualizationSpec } from "@/types";
import { BarChart } from "./charts/bar-chart";
import { LineChart } from "./charts/line-chart";
import { PieDonutChart } from "./charts/pie-donut-chart";
import { ScatterChart } from "./charts/scatter-chart";
import { HistogramChart } from "./charts/histogram-chart";
import { BoxPlotChart } from "./charts/box-plot-chart";
import { KpiCard } from "./charts/kpi-card";
import { DataTable } from "./charts/data-table";
import {
  BarChart2,
  LineChart as LineChartIcon,
  PieChart as PieChartIcon,
  Table as TableIcon,
  Sparkles,
  Download,
  Info,
  Maximize2,
} from "lucide-react";

interface VisualizationRendererProps {
  spec: VisualizationSpec;
  data: Record<string, unknown>[];
  columns?: string[];
  className?: string;
}

export function VisualizationRenderer({
  spec,
  data,
  columns = [],
  className = "",
}: VisualizationRendererProps) {
  const [activeType, setActiveType] = useState<ChartType>(spec.chart_type);
  const [isTableView, setIsTableView] = useState<boolean>(spec.chart_type === "table");
  const containerRef = useRef<HTMLDivElement>(null);

  const availableTypes = spec.available_chart_types && spec.available_chart_types.length > 0
    ? spec.available_chart_types
    : [spec.chart_type, "table" as ChartType];

  const effectiveColumns = columns.length > 0 ? columns : Object.keys(data[0] || {});

  const exportPNG = () => {
    if (!containerRef.current) return;
    const svgElem = containerRef.current.querySelector("svg");
    if (!svgElem) {
      alert("Chart export is supported for SVG visual views.");
      return;
    }

    const svgData = new XMLSerializer().serializeToString(svgElem);
    const canvas = document.createElement("canvas");
    const ctx = canvas.getContext("2d");
    const img = new Image();
    const svgBlob = new Blob([svgData], { type: "image/svg+xml;charset=utf-8" });
    const url = URL.createObjectURL(svgBlob);

    img.onload = () => {
      canvas.width = 800;
      canvas.height = 450;
      if (ctx) {
        ctx.fillStyle = "#FFFFFF";
        ctx.fillRect(0, 0, canvas.width, canvas.height);
        ctx.drawImage(img, 20, 20, 760, 410);
        const pngUrl = canvas.toDataURL("image/png");
        const downloadLink = document.createElement("a");
        downloadLink.href = pngUrl;
        downloadLink.download = `${spec.title.replace(/\s+/g, "_").toLowerCase() || "chart"}.png`;
        document.body.appendChild(downloadLink);
        downloadLink.click();
        document.body.removeChild(downloadLink);
      }
      URL.revokeObjectURL(url);
    };
    img.src = url;
  };

  const renderActiveChart = () => {
    if (isTableView || activeType === "table") {
      return <DataTable columns={effectiveColumns} data={data} title={spec.title} />;
    }

    switch (activeType) {
      case "bar":
        return <BarChart spec={spec} data={data} horizontal={false} />;
      case "horizontal_bar":
        return <BarChart spec={spec} data={data} horizontal={true} />;
      case "line":
        return <LineChart spec={spec} data={data} isArea={false} />;
      case "area":
        return <LineChart spec={spec} data={data} isArea={true} />;
      case "pie":
        return <PieDonutChart spec={spec} data={data} isDonut={false} />;
      case "donut":
        return <PieDonutChart spec={spec} data={data} isDonut={true} />;
      case "scatter":
        return <ScatterChart spec={spec} data={data} />;
      case "histogram":
        return <HistogramChart spec={spec} data={data} />;
      case "boxplot":
        return <BoxPlotChart spec={spec} data={data} />;
      case "kpi":
        return <KpiCard spec={spec} data={data} />;
      default:
        return <DataTable columns={effectiveColumns} data={data} title={spec.title} />;
    }
  };

  return (
    <div
      ref={containerRef}
      className={`flex flex-col border border-border rounded-xl bg-surface shadow-sm overflow-hidden my-3 ${className}`}
    >
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 px-4 py-3 border-b border-border bg-cloud/30">
        <div>
          <div className="flex items-center gap-2">
            <h4 className="text-sm font-bold text-ink tracking-tight">{spec.title}</h4>
            {spec.is_fallback && (
              <span className="text-[10px] font-semibold uppercase bg-amber/10 text-amber px-2 py-0.5 rounded-full border border-amber/20">
                Fallback View
              </span>
            )}
          </div>
          {spec.subtitle && <p className="text-xs text-slate mt-0.5">{spec.subtitle}</p>}
        </div>

        {/* Toolbar Controls */}
        <div className="flex items-center gap-1.5 flex-wrap">
          {/* Chart Type Selector */}
          <div className="flex items-center bg-cloud border border-border rounded-lg p-0.5">
            {availableTypes.map((type) => {
              const isActive = (activeType === type && !isTableView) || (type === "table" && isTableView);
              const isRecommended = type === spec.chart_type;

              return (
                <button
                  key={type}
                  onClick={() => {
                    setActiveType(type);
                    setIsTableView(type === "table");
                  }}
                  className={`flex items-center gap-1 text-xs font-semibold px-2.5 py-1 rounded-md transition-all ${
                    isActive
                      ? "bg-surface text-ink shadow-xs border border-border"
                      : "text-slate hover:text-ink"
                  }`}
                  title={`${type.replace(/_/g, " ").toUpperCase()}${isRecommended ? " (Recommended)" : ""}`}
                >
                  {isRecommended && <Sparkles className="w-3 h-3 text-teal" />}
                  <span className="capitalize">{type.replace(/_/g, " ")}</span>
                </button>
              );
            })}
          </div>

          {/* Export PNG */}
          {!isTableView && activeType !== "table" && activeType !== "kpi" && (
            <button
              onClick={exportPNG}
              className="flex items-center gap-1 text-xs font-medium text-slate hover:text-ink px-2.5 py-1.5 rounded-lg border border-border hover:bg-cloud/60 transition-colors"
              title="Export as PNG image"
            >
              <Download className="w-3.5 h-3.5" />
              <span className="hidden sm:inline">PNG</span>
            </button>
          )}
        </div>
      </div>

      {/* Chart Canvas / Body */}
      <div className="p-4 bg-surface flex flex-col justify-center min-h-[180px]">
        {renderActiveChart()}
      </div>

      {/* Footer / Explanation */}
      {spec.explanation && (
        <div className="flex items-start gap-2 px-4 py-2.5 border-t border-border bg-cloud/20 text-xs text-slate">
          <Info className="w-3.5 h-3.5 text-teal mt-0.5 flex-shrink-0" />
          <span>{spec.explanation}</span>
        </div>
      )}
    </div>
  );
}
