"use client";

import React, { useState } from "react";
import { DatasetProfile } from "@/types";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

interface StatisticsTabProps {
  profile: DatasetProfile | null;
}

export function StatisticsTab({ profile }: StatisticsTabProps) {
  const columns = profile?.column_profiles || [];
  const [selectedColName, setSelectedColName] = useState<string>(
    columns.length > 0 ? columns[0].column_name : ""
  );

  if (!profile || columns.length === 0) {
    return (
      <div className="p-8 text-center text-slate-400 bg-slate-900/30 rounded-xl border border-slate-800">
        No statistical profile available. Run the profiler to compute column statistics.
      </div>
    );
  }

  const selectedCol = columns.find((c) => c.column_name === selectedColName) || columns[0];
  const numStats = selectedCol.numeric_stats;
  const catStats = selectedCol.categorical_stats;
  const tempStats = selectedCol.temporal_stats;
  const boolStats = selectedCol.boolean_stats;

  return (
    <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
      {/* Column Selector List */}
      <div className="lg:col-span-1 space-y-2 max-h-[600px] overflow-y-auto pr-2">
        <div className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2 px-1">
          Select Column
        </div>
        {columns.map((col) => {
          const isSelected = col.column_name === selectedCol.column_name;
          return (
            <button
              key={col.id}
              onClick={() => setSelectedColName(col.column_name)}
              className={`w-full text-left p-3 rounded-xl border transition-all flex items-center justify-between ${
                isSelected
                  ? "bg-indigo-600/10 border-indigo-500/50 text-indigo-200"
                  : "bg-slate-900/40 border-slate-800 text-slate-300 hover:bg-slate-800/50"
              }`}
            >
              <div className="truncate mr-2">
                <div className="text-sm font-medium truncate">{col.column_name}</div>
                <div className="text-xs text-slate-500 font-mono">{col.conceptual_type}</div>
              </div>
              <Badge variant={isSelected ? "blue" : "outline"}>
                {col.conceptual_type}
              </Badge>
            </button>
          );
        })}
      </div>

      {/* Deep Statistics Inspector */}
      <div className="lg:col-span-3 space-y-6">
        <Card className="p-6 bg-slate-900/40 border-slate-800">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-800">
            <div>
              <h3 className="text-lg font-bold text-slate-100">{selectedCol.column_name}</h3>
              <p className="text-xs text-slate-400 mt-1">
                Data Type: <span className="font-mono text-slate-300">{selectedCol.data_type}</span> &bull; Nulls:{" "}
                <span className="text-slate-300">{selectedCol.null_count} ({selectedCol.null_percentage}%)</span> &bull; Uniques:{" "}
                <span className="text-slate-300">{selectedCol.unique_count} ({selectedCol.unique_percentage}%)</span>
              </p>
            </div>
            <Badge variant="blue">
              {selectedCol.conceptual_type}
            </Badge>
          </div>

          {/* 1. Numeric Statistics Matrix */}
          {numStats && (
            <div className="mt-6 space-y-6">
              <div className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
                Descriptive &amp; Quartile Statistics
              </div>
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
                <div className="p-3 bg-slate-950/60 rounded-lg border border-slate-800">
                  <div className="text-xs text-slate-500">Mean</div>
                  <div className="text-lg font-bold text-slate-200 mt-0.5">{numStats.mean}</div>
                </div>
                <div className="p-3 bg-slate-950/60 rounded-lg border border-slate-800">
                  <div className="text-xs text-slate-500">Median (Q2)</div>
                  <div className="text-lg font-bold text-slate-200 mt-0.5">{numStats.median}</div>
                </div>
                <div className="p-3 bg-slate-950/60 rounded-lg border border-slate-800">
                  <div className="text-xs text-slate-500">Min</div>
                  <div className="text-lg font-bold text-slate-200 mt-0.5">{numStats.min}</div>
                </div>
                <div className="p-3 bg-slate-950/60 rounded-lg border border-slate-800">
                  <div className="text-xs text-slate-500">Max</div>
                  <div className="text-lg font-bold text-slate-200 mt-0.5">{numStats.max}</div>
                </div>
                <div className="p-3 bg-slate-950/60 rounded-lg border border-slate-800">
                  <div className="text-xs text-slate-500">Std Deviation</div>
                  <div className="text-lg font-bold text-slate-200 mt-0.5">{numStats.std_dev}</div>
                </div>
                <div className="p-3 bg-slate-950/60 rounded-lg border border-slate-800">
                  <div className="text-xs text-slate-500">Variance</div>
                  <div className="text-lg font-bold text-slate-200 mt-0.5">{numStats.variance}</div>
                </div>
                <div className="p-3 bg-slate-950/60 rounded-lg border border-slate-800">
                  <div className="text-xs text-slate-500">Q1 (25%)</div>
                  <div className="text-lg font-bold text-slate-200 mt-0.5">{numStats.q1}</div>
                </div>
                <div className="p-3 bg-slate-950/60 rounded-lg border border-slate-800">
                  <div className="text-xs text-slate-500">Q3 (75%)</div>
                  <div className="text-lg font-bold text-slate-200 mt-0.5">{numStats.q3}</div>
                </div>
              </div>

              {/* Percentiles Breakdown */}
              {numStats.percentiles && (
                <div className="space-y-2">
                  <div className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
                    Percentiles Distribution
                  </div>
                  <div className="grid grid-cols-3 sm:grid-cols-6 gap-2 text-xs">
                    {Object.entries(numStats.percentiles).map(([p, val]) => (
                      <div key={p} className="p-2 bg-slate-950/40 rounded border border-slate-800/80 text-center">
                        <span className="text-slate-500 font-mono">{p.toUpperCase()}</span>
                        <div className="font-semibold text-slate-200 mt-0.5">{val}</div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Outliers Box */}
              <div className="p-4 bg-slate-950/50 rounded-xl border border-slate-800 flex items-center justify-between">
                <div>
                  <div className="text-sm font-semibold text-slate-200">
                    Tukey IQR Outliers: {selectedCol.outlier_count} detected ({selectedCol.outlier_percentage}%)
                  </div>
                  <div className="text-xs text-slate-400 mt-1">
                    Lower Bound: <span className="font-mono text-slate-300">{numStats.lower_bound}</span> &bull; Upper Bound:{" "}
                    <span className="font-mono text-slate-300">{numStats.upper_bound}</span>
                  </div>
                </div>
                <Badge variant={selectedCol.outlier_count > 0 ? "amber" : "teal"}>
                  {selectedCol.outlier_count > 0 ? "Potential Outliers" : "Clean Range"}
                </Badge>
              </div>
            </div>
          )}

          {/* 2. Categorical Frequencies */}
          {catStats && (
            <div className="mt-6 space-y-4">
              <div className="flex justify-between items-center">
                <div className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
                  Top Frequent Values
                </div>
                <div className="text-xs text-slate-500">
                  Cardinality Ratio: <span className="font-mono text-slate-300">{catStats.cardinality_ratio}</span>
                </div>
              </div>

              <div className="space-y-2">
                {catStats.top_values.map((item, idx) => (
                  <div key={idx} className="p-3 bg-slate-950/50 rounded-lg border border-slate-800 space-y-1">
                    <div className="flex justify-between text-xs">
                      <span className="font-medium text-slate-200 truncate">{item.value}</span>
                      <span className="text-slate-400">
                        {item.count.toLocaleString()} ({item.percentage}%)
                      </span>
                    </div>
                    <div className="w-full bg-slate-800 rounded-full h-1.5 overflow-hidden">
                      <div
                        className="bg-indigo-500 h-1.5 rounded-full"
                        style={{ width: `${item.percentage}%` }}
                      />
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* 3. Temporal Statistics */}
          {tempStats && (
            <div className="mt-6 space-y-4">
              <div className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
                Date Range Boundaries
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div className="p-4 bg-slate-950/50 rounded-lg border border-slate-800">
                  <div className="text-xs text-slate-500">Minimum Date / Start</div>
                  <div className="text-base font-bold text-slate-200 mt-1 font-mono">
                    {tempStats.min_date || "—"}
                  </div>
                </div>
                <div className="p-4 bg-slate-950/50 rounded-lg border border-slate-800">
                  <div className="text-xs text-slate-500">Maximum Date / End</div>
                  <div className="text-base font-bold text-slate-200 mt-1 font-mono">
                    {tempStats.max_date || "—"}
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* 4. Boolean Statistics */}
          {boolStats && (
            <div className="mt-6 space-y-4">
              <div className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
                Boolean Truth Distribution
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div className="p-4 bg-slate-950/50 rounded-lg border border-slate-800">
                  <div className="text-xs text-slate-500">True Count</div>
                  <div className="text-xl font-bold text-emerald-400 mt-1">
                    {boolStats.true_count} ({boolStats.true_percentage}%)
                  </div>
                </div>
                <div className="p-4 bg-slate-950/50 rounded-lg border border-slate-800">
                  <div className="text-xs text-slate-500">False Count</div>
                  <div className="text-xl font-bold text-slate-300 mt-1">
                    {boolStats.false_count} ({boolStats.false_percentage}%)
                  </div>
                </div>
              </div>
            </div>
          )}
        </Card>
      </div>
    </div>
  );
}
