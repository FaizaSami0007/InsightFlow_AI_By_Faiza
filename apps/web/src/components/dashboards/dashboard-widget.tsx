"use client";

import React, { useState } from "react";
import { DashboardWidget, ChartType } from "@/types";
import { VisualizationRenderer } from "@/components/visualization/visualization-renderer";
import {
  Trash2,
  Info,
  Database,
  AlertCircle,
} from "lucide-react";
import { Dialog } from "@/components/ui/dialog";

interface DashboardWidgetCardProps {
  widget: DashboardWidget;
  isEditMode: boolean;
  onRemove?: () => void;
  onChangeChartType?: (chartType: ChartType) => void;
  onResize?: (gridW: number, gridH: number) => void;
  onMove?: (direction: "up" | "down" | "left" | "right") => void;
  onInspectProvenance?: (widget: DashboardWidget) => void;
}

export function DashboardWidgetCard({
  widget,
  isEditMode,
  onRemove,
  onChangeChartType,
  onResize,
  onMove,
  onInspectProvenance,
}: DashboardWidgetCardProps) {
  const [showEvidence, setShowEvidence] = useState(false);

  const rows = widget.result_data?.rows || [];
  const columns = widget.result_data?.columns || [];
  const hasSpec = !!widget.chart_spec;
  const isFailed = widget.metadata?.status === "FAILED" || (!hasSpec && !widget.analysis_id);

  // Convert 12-column grid_w to Tailwind col-span class
  const colSpanClass =
    widget.grid_w >= 12
      ? "col-span-12"
      : widget.grid_w >= 8
      ? "col-span-12 lg:col-span-8"
      : widget.grid_w >= 6
      ? "col-span-12 md:col-span-6"
      : widget.grid_w >= 4
      ? "col-span-12 md:col-span-6 lg:col-span-4"
      : "col-span-12 md:col-span-6 lg:col-span-3";

  return (
    <div
      className={`${colSpanClass} bg-white rounded-xl border border-[#E3E8EF] shadow-sm hover:shadow-md transition-all flex flex-col overflow-hidden relative ${
        isEditMode ? "ring-2 ring-teal ring-offset-1" : ""
      }`}
      style={{ minHeight: widget.grid_h ? `${widget.grid_h * 75}px` : "240px" }}
    >
      {/* Widget Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-[#E3E8EF] bg-white">
        <div className="min-w-0 pr-2">
          <div className="flex items-center gap-2">
            <h3 className="text-sm font-semibold text-[#172033] truncate" title={widget.title}>
              {widget.title}
            </h3>
            {widget.widget_type === "kpi" && (
              <span className="px-1.5 py-0.5 text-[10px] font-semibold bg-[#E6F4F1] text-[#0F766E] rounded">
                KPI
              </span>
            )}
          </div>
          {widget.description && (
            <p className="text-xs text-[#536176] truncate mt-0.5" title={widget.description}>
              {widget.description}
            </p>
          )}
        </div>

        <div className="flex items-center gap-1 shrink-0">
          {/* Provenance Badge */}
          <button
            type="button"
            onClick={() => {
              if (onInspectProvenance) {
                onInspectProvenance(widget);
              } else {
                setShowEvidence(true);
              }
            }}
            className="p-1.5 text-[#536176] hover:text-[#0F766E] hover:bg-[#F7F9FC] rounded-md transition-colors"
            title="Inspect Analytical Provenance"
          >
            <Info className="w-3.5 h-3.5" />
          </button>

          {isEditMode && (
            <>
              {/* Resize options */}
              <select
                value={widget.grid_w}
                onChange={(e) => onResize && onResize(Number(e.target.value), widget.grid_h)}
                className="text-xs bg-[#F7F9FC] border border-[#E3E8EF] rounded px-1.5 py-0.5 text-[#172033] cursor-pointer"
                title="Change Column Width"
              >
                <option value={3} className="text-slate-800 bg-white font-medium">Span 3</option>
                <option value={4} className="text-slate-800 bg-white font-medium">Span 4</option>
                <option value={6} className="text-slate-800 bg-white font-medium">Span 6</option>
                <option value={8} className="text-slate-800 bg-white font-medium">Span 8</option>
                <option value={12} className="text-slate-800 bg-white font-medium">Span 12</option>
              </select>

              {/* Chart type dropdown if visual */}
              {widget.chart_spec && (
                <select
                  value={widget.chart_spec.chart_type}
                  onChange={(e) =>
                    onChangeChartType && onChangeChartType(e.target.value as ChartType)
                  }
                  className="text-xs bg-[#F7F9FC] border border-[#E3E8EF] rounded px-1.5 py-0.5 text-[#172033] cursor-pointer"
                  title="Change Visualization Type"
                >
                  <option value="bar" className="text-slate-800 bg-white font-medium">Bar</option>
                  <option value="horizontal_bar" className="text-slate-800 bg-white font-medium">Horiz Bar</option>
                  <option value="line" className="text-slate-800 bg-white font-medium">Line</option>
                  <option value="area" className="text-slate-800 bg-white font-medium">Area</option>
                  <option value="donut" className="text-slate-800 bg-white font-medium">Donut</option>
                  <option value="pie" className="text-slate-800 bg-white font-medium">Pie</option>
                  <option value="scatter" className="text-slate-800 bg-white font-medium">Scatter</option>
                  <option value="histogram" className="text-slate-800 bg-white font-medium">Histogram</option>
                  <option value="boxplot" className="text-slate-800 bg-white font-medium">Boxplot</option>
                  <option value="table" className="text-slate-800 bg-white font-medium">Table</option>
                </select>
              )}

              {/* Remove widget */}
              <button
                type="button"
                onClick={() => onRemove && onRemove()}
                className="p-1.5 text-red-500 hover:bg-red-50 rounded-md transition-colors"
                title="Remove Widget"
              >
                <Trash2 className="w-3.5 h-3.5" />
              </button>
            </>
          )}
        </div>
      </div>

      {/* Widget Body */}
      <div className="p-4 flex-1 flex flex-col justify-center overflow-auto">
        {isFailed ? (
          <div className="flex flex-col items-center justify-center text-center p-6 text-amber-700 bg-amber-50/50 rounded-lg border border-amber-200">
            <AlertCircle className="w-6 h-6 mb-2 text-amber-600" />
            <p className="text-xs font-semibold">Analytical Result Unavailable</p>
            <p className="text-[11px] text-amber-600 mt-1">
              {(widget.metadata?.error as string) || "Widget calculation could not complete."}
            </p>
          </div>
        ) : hasSpec ? (
          <div className="w-full h-full flex-1">
            <VisualizationRenderer
              spec={widget.chart_spec!}
              data={rows}
              columns={columns}
              className="border-none shadow-none p-0"
            />
          </div>
        ) : (
          <div className="text-center text-xs text-[#536176] py-8">
            No chart specification defined.
          </div>
        )}
      </div>

      {/* Provenance Footer */}
      <div className="px-4 py-1.5 bg-[#F7F9FC] border-t border-[#E3E8EF] flex items-center justify-between text-[11px] text-[#536176]">
        <span className="truncate">
          {widget.analysis_id ? `Analysis #${widget.analysis_id.slice(0, 8)}` : "Direct Metric"}
        </span>
        <span>{rows.length > 0 ? `${rows.length} rows` : ""}</span>
      </div>

      {/* Analytical Provenance Modal */}
      <Dialog
        isOpen={showEvidence}
        onClose={() => setShowEvidence(false)}
        title={`Analytical Evidence: ${widget.title}`}
        description="Deterministic audit trail and underlying query output for this widget."
      >
        <div className="space-y-4 text-xs text-[#172033] mt-2">
          <div className="grid grid-cols-2 gap-3 p-3 bg-[#F7F9FC] rounded-lg border border-[#E3E8EF]">
            <div>
              <span className="text-[#536176] block text-[11px]">Analysis Job ID</span>
              <span className="font-mono font-semibold">{widget.analysis_id || "None"}</span>
            </div>
            <div>
              <span className="text-[#536176] block text-[11px]">Execution Status</span>
              <span className="font-semibold text-[#0F766E]">
                {widget.analysis_status || "COMPLETED"}
              </span>
            </div>
            <div>
              <span className="text-[#536176] block text-[11px]">Widget Type</span>
              <span className="font-medium capitalize">{widget.widget_type}</span>
            </div>
            <div>
              <span className="text-[#536176] block text-[11px]">Chart Type</span>
              <span className="font-medium">{widget.chart_spec?.chart_type || "N/A"}</span>
            </div>
          </div>

          {widget.chart_spec?.explanation && (
            <div className="p-3 bg-blue-50 border border-blue-200 rounded-lg text-blue-900">
              <span className="font-semibold block mb-0.5">Visualization Rationale:</span>
              {widget.chart_spec.explanation}
            </div>
          )}

          <div>
            <h4 className="font-semibold text-xs text-[#172033] mb-1.5">Result Sample (First 5 Rows):</h4>
            {rows.length > 0 ? (
              <div className="overflow-x-auto border border-[#E3E8EF] rounded-lg">
                <table className="w-full text-left text-xs border-collapse">
                  <thead className="bg-[#F7F9FC] border-b border-[#E3E8EF]">
                    <tr>
                      {columns.map((c) => (
                        <th key={c} className="px-3 py-1.5 font-semibold text-[#536176]">
                          {c}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-[#E3E8EF]">
                    {rows.slice(0, 5).map((r, rIdx) => (
                      <tr key={rIdx} className="hover:bg-slate-50">
                        {columns.map((c) => (
                          <td key={c} className="px-3 py-1.5">
                            {String(r[c] ?? "")}
                          </td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <p className="text-[#536176]">No result records available.</p>
            )}
          </div>
        </div>
      </Dialog>
    </div>
  );
}
