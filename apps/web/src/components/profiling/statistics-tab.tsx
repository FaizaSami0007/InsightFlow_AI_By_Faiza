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
      <div className="p-8 text-center text-slate bg-surface rounded-xl border border-border shadow-soft">
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
        <div className="text-xs font-semibold text-slate uppercase tracking-wider mb-2 px-1">
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
                  ? "bg-teal-soft border-teal-border text-teal font-semibold shadow-soft"
                  : "bg-surface border-border text-ink hover:bg-cloud-subtle hover:border-border-strong"
              }`}
            >
              <div className="truncate mr-2">
                <div className="text-sm font-medium truncate">{col.column_name}</div>
                <div className="text-xs text-slate font-mono">{col.conceptual_type}</div>
              </div>
              <Badge variant={isSelected ? "teal" : "outline"}>
                {col.conceptual_type}
              </Badge>
            </button>
          );
        })}
      </div>

      {/* Deep Statistics Inspector */}
      <div className="lg:col-span-3 space-y-6">
        <Card className="p-6 bg-surface border-border shadow-soft">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-border">
            <div>
              <h3 className="text-lg font-bold text-ink">{selectedCol.column_name}</h3>
              <p className="text-xs text-slate mt-1">
                Data Type: <span className="font-mono font-medium text-ink">{selectedCol.data_type}</span> &bull; Nulls:{" "}
                <span className="font-medium text-ink">{selectedCol.null_count} ({selectedCol.null_percentage}%)</span> &bull; Uniques:{" "}
                <span className="font-medium text-ink">{selectedCol.unique_count} ({selectedCol.unique_percentage}%)</span>
              </p>
            </div>
            <Badge variant="teal">
              {selectedCol.conceptual_type}
            </Badge>
          </div>

          {/* 1. Numeric Statistics Matrix */}
          {numStats && (
            <div className="mt-6 space-y-6">
              <div className="text-xs font-semibold text-slate uppercase tracking-wider">
                Descriptive &amp; Quartile Statistics
              </div>
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
                <div className="p-3 bg-cloud rounded-xl border border-border">
                  <div className="text-xs text-slate">Mean</div>
                  <div className="text-lg font-bold text-ink mt-0.5">{numStats.mean}</div>
                </div>
                <div className="p-3 bg-cloud rounded-xl border border-border">
                  <div className="text-xs text-slate">Median (Q2)</div>
                  <div className="text-lg font-bold text-ink mt-0.5">{numStats.median}</div>
                </div>
                <div className="p-3 bg-cloud rounded-xl border border-border">
                  <div className="text-xs text-slate">Min</div>
                  <div className="text-lg font-bold text-ink mt-0.5">{numStats.min}</div>
                </div>
                <div className="p-3 bg-cloud rounded-xl border border-border">
                  <div className="text-xs text-slate">Max</div>
                  <div className="text-lg font-bold text-ink mt-0.5">{numStats.max}</div>
                </div>
                <div className="p-3 bg-cloud rounded-xl border border-border">
                  <div className="text-xs text-slate">Std Deviation</div>
                  <div className="text-lg font-bold text-ink mt-0.5">{numStats.std_dev}</div>
                </div>
                <div className="p-3 bg-cloud rounded-xl border border-border">
                  <div className="text-xs text-slate">Variance</div>
                  <div className="text-lg font-bold text-ink mt-0.5">{numStats.variance}</div>
                </div>
                <div className="p-3 bg-cloud rounded-xl border border-border">
                  <div className="text-xs text-slate">Q1 (25%)</div>
                  <div className="text-lg font-bold text-ink mt-0.5">{numStats.q1}</div>
                </div>
                <div className="p-3 bg-cloud rounded-xl border border-border">
                  <div className="text-xs text-slate">Q3 (75%)</div>
                  <div className="text-lg font-bold text-ink mt-0.5">{numStats.q3}</div>
                </div>
              </div>

              {/* Percentiles Breakdown */}
              {numStats.percentiles && (
                <div className="space-y-2">
                  <div className="text-xs font-semibold text-slate uppercase tracking-wider">
                    Percentiles Distribution
                  </div>
                  <div className="grid grid-cols-3 sm:grid-cols-6 gap-2 text-xs">
                    {Object.entries(numStats.percentiles).map(([p, val]) => (
                      <div key={p} className="p-2.5 bg-cloud rounded-lg border border-border text-center">
                        <span className="text-slate font-mono text-[11px]">{p.toUpperCase()}</span>
                        <div className="font-bold text-ink mt-0.5">{val}</div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Outliers Box */}
              <div className="p-4 bg-cloud rounded-xl border border-border flex items-center justify-between">
                <div>
                  <div className="text-sm font-semibold text-ink">
                    Tukey IQR Outliers: {selectedCol.outlier_count} detected ({selectedCol.outlier_percentage}%)
                  </div>
                  <div className="text-xs text-slate mt-1">
                    Lower Bound: <span className="font-mono font-medium text-ink">{numStats.lower_bound}</span> &bull; Upper Bound:{" "}
                    <span className="font-mono font-medium text-ink">{numStats.upper_bound}</span>
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
                <div className="text-xs font-semibold text-slate uppercase tracking-wider">
                  Top Frequent Values
                </div>
                <div className="text-xs text-slate">
                  Cardinality Ratio: <span className="font-mono font-medium text-ink">{catStats.cardinality_ratio}</span>
                </div>
              </div>

              <div className="space-y-2">
                {catStats.top_values.map((item, idx) => (
                  <div key={idx} className="p-3 bg-cloud rounded-xl border border-border space-y-1.5">
                    <div className="flex justify-between text-xs">
                      <span className="font-semibold text-ink truncate">{item.value}</span>
                      <span className="text-slate font-mono">
                        {item.count.toLocaleString()} ({item.percentage}%)
                      </span>
                    </div>
                    <div className="w-full bg-cloud-subtle rounded-full h-2 overflow-hidden border border-border-subtle">
                      <div
                        className="bg-teal h-2 rounded-full transition-all"
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
              <div className="text-xs font-semibold text-slate uppercase tracking-wider">
                Date Range Boundaries
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div className="p-4 bg-cloud rounded-xl border border-border">
                  <div className="text-xs text-slate">Minimum Date / Start</div>
                  <div className="text-base font-bold text-ink mt-1 font-mono">
                    {tempStats.min_date || "—"}
                  </div>
                </div>
                <div className="p-4 bg-cloud rounded-xl border border-border">
                  <div className="text-xs text-slate">Maximum Date / End</div>
                  <div className="text-base font-bold text-ink mt-1 font-mono">
                    {tempStats.max_date || "—"}
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* 4. Boolean Statistics */}
          {boolStats && (
            <div className="mt-6 space-y-4">
              <div className="text-xs font-semibold text-slate uppercase tracking-wider">
                Boolean Truth Distribution
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div className="p-4 bg-cloud rounded-xl border border-border">
                  <div className="text-xs text-slate">True Count</div>
                  <div className="text-xl font-bold text-teal mt-1">
                    {boolStats.true_count} ({boolStats.true_percentage}%)
                  </div>
                </div>
                <div className="p-4 bg-cloud rounded-xl border border-border">
                  <div className="text-xs text-slate">False Count</div>
                  <div className="text-xl font-bold text-ink mt-1">
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
