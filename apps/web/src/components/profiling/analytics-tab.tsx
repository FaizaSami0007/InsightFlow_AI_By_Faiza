"use client";

import React, { useState } from "react";
import {
  AnalysisResponse,
  ColumnProfile,
  DatasetProfile,
  SemanticColumn,
} from "@/types";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Play,
  RotateCcw,
  Sparkles,
  Table as TableIcon,
  Clock,
  CheckCircle2,
  AlertTriangle,
  Layers,
  BarChart3,
  TrendingUp,
  Activity,
  Filter,
} from "lucide-react";

interface AnalyticsTabProps {
  datasetId: string;
  versionId: string;
  profile: DatasetProfile | null;
}

type OperationType =
  | "group_by"
  | "describe_dataset"
  | "correlation"
  | "distribution"
  | "time_series_summary"
  | "percent_change"
  | "frequency"
  | "compare_groups"
  | "outlier_analysis";

export function AnalyticsTab({ datasetId, versionId, profile }: AnalyticsTabProps) {
  const [operation, setOperation] = useState<OperationType>("group_by");
  const [dimension, setDimension] = useState<string>("");
  const [metric, setMetric] = useState<string>("");
  const [aggregation, setAggregation] = useState<string>("SUM");
  const [selectedColumns, setSelectedColumns] = useState<string[]>([]);
  const [dateColumn, setDateColumn] = useState<string>("");
  const [period, setPeriod] = useState<string>("month");
  const [bins, setBins] = useState<number>(10);
  const [topN, setTopN] = useState<number>(10);

  // Filter state
  const [filterColumn, setFilterColumn] = useState<string>("");
  const [filterOperator, setFilterOperator] = useState<string>("=");
  const [filterValue, setFilterValue] = useState<string>("");

  // Execution state
  const [loading, setLoading] = useState<boolean>(false);
  const [result, setResult] = useState<AnalysisResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const columnProfiles = profile?.column_profiles || [];
  const semanticColumns = profile?.semantic_columns || [];

  // Filter columns by semantic/conceptual type for HCI error prevention
  const numericColumns = columnProfiles
    .filter(
      (c) =>
        c.conceptual_type === "INTEGER" ||
        c.conceptual_type === "FLOAT" ||
        c.numeric_stats !== null
    )
    .map((c) => c.column_name);

  const dimensionColumns = columnProfiles
    .filter(
      (c) =>
        c.conceptual_type === "STRING" ||
        c.conceptual_type === "BOOLEAN" ||
        c.conceptual_type === "DATE" ||
        c.unique_count <= 100
    )
    .map((c) => c.column_name);

  const dateColumns = columnProfiles
    .filter(
      (c) =>
        c.conceptual_type === "DATE" ||
        c.conceptual_type === "DATETIME" ||
        c.temporal_stats !== null
    )
    .map((c) => c.column_name);

  const allColumns = columnProfiles.map((c) => c.column_name);

  // Initialize sensible defaults if empty
  React.useEffect(() => {
    if (dimensionColumns.length > 0) {
      setDimension((prev) => prev || dimensionColumns[0]);
    }
    if (numericColumns.length > 0) {
      setMetric((prev) => prev || numericColumns[0]);
    }
    if (dateColumns.length > 0) {
      setDateColumn((prev) => prev || dateColumns[0]);
    }
    if (numericColumns.length >= 2) {
      setSelectedColumns((prev) => (prev.length === 0 ? numericColumns.slice(0, 3) : prev));
    }
  }, [columnProfiles.length, dimensionColumns, numericColumns, dateColumns]);

  const handleRunAnalysis = async () => {
    setLoading(true);
    setError(null);

    const token = localStorage.getItem("token");
    let parameters: Record<string, unknown> = {};

    if (operation === "group_by") {
      parameters = {
        dimensions: [dimension || allColumns[0]],
        aggregations: [
          {
            column: metric || "*",
            agg_type: aggregation,
            alias: `${metric || "records"}_${aggregation.toLowerCase()}`,
          },
          { column: "*", agg_type: "COUNT", alias: "count" },
        ],
      };
    } else if (operation === "describe_dataset") {
      parameters = { columns: selectedColumns.length > 0 ? selectedColumns : undefined };
    } else if (operation === "correlation") {
      parameters = {
        columns: selectedColumns.length >= 2 ? selectedColumns : numericColumns.slice(0, 3),
        method: "pearson",
      };
    } else if (operation === "distribution") {
      parameters = { column: metric || numericColumns[0], bins: Number(bins) };
    } else if (operation === "time_series_summary") {
      parameters = {
        date_column: dateColumn || dateColumns[0] || allColumns[0],
        metric_column: metric || undefined,
        period,
        aggregation,
      };
    } else if (operation === "percent_change") {
      parameters = {
        metric_column: metric || numericColumns[0],
        order_by_column: dateColumn || dateColumns[0] || allColumns[0],
      };
    } else if (operation === "frequency") {
      parameters = { column: dimension || allColumns[0], top_n: Number(topN) };
    } else if (operation === "compare_groups") {
      parameters = {
        dimension: dimension || allColumns[0],
        metric: metric || numericColumns[0],
        aggregation,
      };
    } else if (operation === "outlier_analysis") {
      parameters = { column: metric || numericColumns[0], multiplier: 1.5 };
    }

    let filterPayload = undefined;
    if (filterColumn && filterValue.trim()) {
      filterPayload = {
        column: filterColumn,
        operator: filterOperator,
        value: isNaN(Number(filterValue)) ? filterValue : Number(filterValue),
      };
    }

    try {
      const res = await fetch("http://localhost:8000/api/v1/analytics/run", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        body: JSON.stringify({
          dataset_id: datasetId,
          dataset_version_id: versionId,
          operation,
          parameters,
          filters: filterPayload,
        }),
      });

      if (!res.ok) {
        const errData = await res.json().catch(() => ({}));
        throw new Error(errData?.detail || errData?.error?.message || "Analysis execution failed");
      }

      const data: AnalysisResponse = await res.json();
      setResult(data);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Analysis failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Top Header Banner */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 p-4 rounded-xl bg-gradient-to-r from-teal-900/30 via-slate-900/40 to-slate-900/20 border border-teal-500/20">
        <div>
          <div className="flex items-center gap-2">
            <Sparkles className="w-5 h-5 text-teal-400" />
            <h3 className="font-semibold text-white text-base">Deterministic Analytics Engine</h3>
            <Badge variant="teal">DuckDB Powered</Badge>
          </div>
          <p className="text-xs text-slate-400 mt-1">
            Execute verified mathematical computations, aggregations, distributions, and statistical models.
          </p>
        </div>

        <Button
          onClick={handleRunAnalysis}
          disabled={loading}
          className="bg-teal-500 hover:bg-teal-400 text-slate-950 font-semibold shadow-lg shadow-teal-500/20 gap-2"
        >
          {loading ? (
            <>
              <RotateCcw className="w-4 h-4 animate-spin" />
              Running Analysis...
            </>
          ) : (
            <>
              <Play className="w-4 h-4 fill-current" />
              Execute Analysis
            </>
          )}
        </Button>
      </div>

      {/* Analytics Configuration Controls Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Step 1: Operation Selection */}
        <Card className="bg-slate-900/60 border-slate-800">
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-semibold text-slate-200 flex items-center gap-2">
              <Layers className="w-4 h-4 text-teal-400" />
              1. Analytical Tool
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <label className="text-xs text-slate-400 font-medium">Select Analysis Operation</label>
            <select
              value={operation}
              onChange={(e) => {
                setOperation(e.target.value as OperationType);
                setResult(null);
                setError(null);
              }}
              className="w-full bg-slate-950 border border-slate-800 rounded-lg p-2.5 text-sm text-slate-200 focus:outline-none focus:border-teal-500"
            >
              <optgroup label="Aggregation & Grouping">
                <option value="group_by">Group By & Aggregate</option>
                <option value="compare_groups">Compare Discrete Groups</option>
                <option value="frequency">Category Frequency Distribution</option>
              </optgroup>
              <optgroup label="Statistical Analysis">
                <option value="describe_dataset">Describe Summary Statistics</option>
                <option value="correlation">Pairwise Correlation Matrix</option>
                <option value="distribution">Distribution & Histogram</option>
                <option value="outlier_analysis">Tukey IQR Outlier Analysis</option>
              </optgroup>
              <optgroup label="Temporal Analysis">
                <option value="time_series_summary">Time Series Trend Summary</option>
                <option value="percent_change">Sequential Percent Change</option>
              </optgroup>
            </select>

            <p className="text-[11px] text-slate-500 leading-relaxed">
              {operation === "group_by" && "Groups records by dimension keys and computes SQL sums, averages, and counts."}
              {operation === "describe_dataset" && "Calculates quartiles, means, standard deviations, and missing counts."}
              {operation === "correlation" && "Calculates Pearson correlation coefficients and sample sizes."}
              {operation === "distribution" && "Computes moments (skewness, kurtosis) and histogram frequency bins."}
              {operation === "time_series_summary" && "Aggregates metrics over date truncation intervals (day, week, month, year)."}
              {operation === "percent_change" && "Calculates period-over-period delta and growth rate percentages."}
              {operation === "frequency" && "Analyzes category proportions and cumulative frequency distributions."}
              {operation === "compare_groups" && "Compares key metric performance across category groups."}
              {operation === "outlier_analysis" && "Extracts statistical outliers exceeding 1.5x IQR threshold bounds."}
            </p>
          </CardContent>
        </Card>

        {/* Step 2: Parameter Configuration */}
        <Card className="bg-slate-900/60 border-slate-800">
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-semibold text-slate-200 flex items-center gap-2">
              <BarChart3 className="w-4 h-4 text-blue-400" />
              2. Target Parameters
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            {/* Group By Parameters */}
            {operation === "group_by" && (
              <>
                <div>
                  <label className="text-xs text-slate-400 font-medium">Group Dimension</label>
                  <select
                    value={dimension}
                    onChange={(e) => setDimension(e.target.value)}
                    className="w-full mt-1 bg-slate-950 border border-slate-800 rounded-lg p-2 text-sm text-slate-200 focus:outline-none focus:border-teal-500"
                  >
                    {allColumns.map((c) => (
                      <option key={c} value={c}>
                        {c}
                      </option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="text-xs text-slate-400 font-medium">Target Metric</label>
                  <select
                    value={metric}
                    onChange={(e) => setMetric(e.target.value)}
                    className="w-full mt-1 bg-slate-950 border border-slate-800 rounded-lg p-2 text-sm text-slate-200 focus:outline-none focus:border-teal-500"
                  >
                    {numericColumns.map((c) => (
                      <option key={c} value={c}>
                        {c} (Numeric)
                      </option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="text-xs text-slate-400 font-medium">Aggregation Function</label>
                  <select
                    value={aggregation}
                    onChange={(e) => setAggregation(e.target.value)}
                    className="w-full mt-1 bg-slate-950 border border-slate-800 rounded-lg p-2 text-sm text-slate-200 focus:outline-none focus:border-teal-500"
                  >
                    <option value="SUM">SUM</option>
                    <option value="AVG">AVG (Average)</option>
                    <option value="MEDIAN">MEDIAN</option>
                    <option value="MIN">MIN</option>
                    <option value="MAX">MAX</option>
                    <option value="STDDEV">STDDEV (Standard Dev)</option>
                  </select>
                </div>
              </>
            )}

            {/* Correlation Parameters */}
            {operation === "correlation" && (
              <div>
                <label className="text-xs text-slate-400 font-medium">Select Numeric Columns (2+)</label>
                <div className="mt-1 space-y-1.5 max-h-40 overflow-y-auto p-2 bg-slate-950 border border-slate-800 rounded-lg">
                  {numericColumns.map((c) => (
                    <label key={c} className="flex items-center gap-2 text-xs text-slate-300 cursor-pointer">
                      <input
                        type="checkbox"
                        checked={selectedColumns.includes(c)}
                        onChange={(e) => {
                          if (e.target.checked) {
                            setSelectedColumns([...selectedColumns, c]);
                          } else {
                            setSelectedColumns(selectedColumns.filter((col) => col !== c));
                          }
                        }}
                        className="rounded border-slate-700 text-teal-500 focus:ring-teal-500"
                      />
                      {c}
                    </label>
                  ))}
                </div>
              </div>
            )}

            {/* Distribution Parameters */}
            {operation === "distribution" && (
              <>
                <div>
                  <label className="text-xs text-slate-400 font-medium">Numeric Column</label>
                  <select
                    value={metric}
                    onChange={(e) => setMetric(e.target.value)}
                    className="w-full mt-1 bg-slate-950 border border-slate-800 rounded-lg p-2 text-sm text-slate-200 focus:outline-none focus:border-teal-500"
                  >
                    {numericColumns.map((c) => (
                      <option key={c} value={c}>
                        {c}
                      </option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="text-xs text-slate-400 font-medium">Histogram Bins ({bins})</label>
                  <input
                    type="range"
                    min="4"
                    max="30"
                    value={bins}
                    onChange={(e) => setBins(Number(e.target.value))}
                    className="w-full mt-1 accent-teal-500"
                  />
                </div>
              </>
            )}

            {/* Time Series Parameters */}
            {operation === "time_series_summary" && (
              <>
                <div>
                  <label className="text-xs text-slate-400 font-medium">Date / Time Column</label>
                  <select
                    value={dateColumn}
                    onChange={(e) => setDateColumn(e.target.value)}
                    className="w-full mt-1 bg-slate-950 border border-slate-800 rounded-lg p-2 text-sm text-slate-200 focus:outline-none focus:border-teal-500"
                  >
                    {allColumns.map((c) => (
                      <option key={c} value={c}>
                        {c}
                      </option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="text-xs text-slate-400 font-medium">Period Granularity</label>
                  <select
                    value={period}
                    onChange={(e) => setPeriod(e.target.value)}
                    className="w-full mt-1 bg-slate-950 border border-slate-800 rounded-lg p-2 text-sm text-slate-200 focus:outline-none focus:border-teal-500"
                  >
                    <option value="day">Day</option>
                    <option value="week">Week</option>
                    <option value="month">Month</option>
                    <option value="quarter">Quarter</option>
                    <option value="year">Year</option>
                  </select>
                </div>
                <div>
                  <label className="text-xs text-slate-400 font-medium">Metric (Optional)</label>
                  <select
                    value={metric}
                    onChange={(e) => setMetric(e.target.value)}
                    className="w-full mt-1 bg-slate-950 border border-slate-800 rounded-lg p-2 text-sm text-slate-200 focus:outline-none focus:border-teal-500"
                  >
                    <option value="">Count Only</option>
                    {numericColumns.map((c) => (
                      <option key={c} value={c}>
                        {c} (SUM)
                      </option>
                    ))}
                  </select>
                </div>
              </>
            )}

            {/* Frequency / Compare / Outlier Fallbacks */}
            {(operation === "frequency" || operation === "compare_groups" || operation === "outlier_analysis" || operation === "percent_change") && (
              <div>
                <label className="text-xs text-slate-400 font-medium">Target Column</label>
                <select
                  value={operation === "frequency" ? dimension : metric}
                  onChange={(e) => (operation === "frequency" ? setDimension(e.target.value) : setMetric(e.target.value))}
                  className="w-full mt-1 bg-slate-950 border border-slate-800 rounded-lg p-2 text-sm text-slate-200 focus:outline-none focus:border-teal-500"
                >
                  {(operation === "frequency" ? allColumns : numericColumns).map((c) => (
                    <option key={c} value={c}>
                      {c}
                    </option>
                  ))}
                </select>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Step 3: Optional Filter Predicate */}
        <Card className="bg-slate-900/60 border-slate-800">
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-semibold text-slate-200 flex items-center gap-2">
              <Filter className="w-4 h-4 text-purple-400" />
              3. Scope Filters (Optional)
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <div>
              <label className="text-xs text-slate-400 font-medium">Filter Column</label>
              <select
                value={filterColumn}
                onChange={(e) => setFilterColumn(e.target.value)}
                className="w-full mt-1 bg-slate-950 border border-slate-800 rounded-lg p-2 text-sm text-slate-200 focus:outline-none focus:border-teal-500"
              >
                <option value="">No Filter Applied</option>
                {allColumns.map((c) => (
                  <option key={c} value={c}>
                    {c}
                  </option>
                ))}
              </select>
            </div>

            {filterColumn && (
              <div className="grid grid-cols-2 gap-2">
                <div>
                  <label className="text-xs text-slate-400 font-medium">Operator</label>
                  <select
                    value={filterOperator}
                    onChange={(e) => setFilterOperator(e.target.value)}
                    className="w-full mt-1 bg-slate-950 border border-slate-800 rounded-lg p-2 text-xs text-slate-200 focus:outline-none"
                  >
                    <option value="=">=</option>
                    <option value="!=">!=</option>
                    <option value=">">&gt;</option>
                    <option value=">=">&gt;=</option>
                    <option value="<">&lt;</option>
                    <option value="<=">&lt;=</option>
                  </select>
                </div>
                <div>
                  <label className="text-xs text-slate-400 font-medium">Value</label>
                  <input
                    type="text"
                    value={filterValue}
                    onChange={(e) => setFilterValue(e.target.value)}
                    placeholder="e.g. North, 100"
                    className="w-full mt-1 bg-slate-950 border border-slate-800 rounded-lg p-2 text-xs text-slate-200 focus:outline-none focus:border-teal-500"
                  />
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Error Display */}
      {error && (
        <div className="p-4 rounded-xl bg-red-950/40 border border-red-500/30 flex items-start gap-3">
          <AlertTriangle className="w-5 h-5 text-red-400 mt-0.5 shrink-0" />
          <div>
            <h4 className="text-sm font-semibold text-red-200">Analysis Error</h4>
            <p className="text-xs text-red-300/90 mt-0.5">{error}</p>
          </div>
        </div>
      )}

      {/* Results View */}
      {result && (
        <div className="space-y-6">
          {/* Metadata & Performance Bar */}
          <div className="flex flex-wrap items-center justify-between gap-4 p-4 rounded-xl bg-slate-900/60 border border-slate-800">
            <div className="flex items-center gap-3">
              <CheckCircle2 className="w-5 h-5 text-teal-400" />
              <div>
                <span className="text-sm font-medium text-white capitalize">{result.operation.replace(/_/g, " ")} Result</span>
                <span className="text-xs text-slate-400 ml-2">({result.row_count} rows returned)</span>
              </div>
            </div>

            <div className="flex items-center gap-4 text-xs">
              <span className="flex items-center gap-1.5 text-slate-300">
                <Clock className="w-3.5 h-3.5 text-teal-400" />
                Execution: <strong>{result.execution_time_ms} ms</strong>
              </span>
              <Badge variant="outline" className="text-[11px] font-mono">
                ID: {result.analysis_id.slice(0, 8)}...
              </Badge>
            </div>
          </div>

          {/* Summary KPIs if present */}
          {result.summary && Object.keys(result.summary).length > 0 && (
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
              {Object.entries(result.summary)
                .slice(0, 4)
                .map(([k, v]) => (
                  <Card key={k} className="bg-slate-900/40 border-slate-800/80">
                    <CardContent className="p-4">
                      <span className="text-xs text-slate-400 capitalize">{k.replace(/_/g, " ")}</span>
                      <p className="text-lg font-semibold text-white mt-1 truncate">
                        {v !== null && v !== undefined ? String(v) : "—"}
                      </p>
                    </CardContent>
                  </Card>
                ))}
            </div>
          )}

          {/* Tabular Result View */}
          <Card className="bg-slate-900/60 border-slate-800">
            <CardHeader className="pb-3 border-b border-slate-800/60">
              <CardTitle className="text-sm font-semibold text-slate-200 flex items-center gap-2">
                <TableIcon className="w-4 h-4 text-teal-400" />
                Structured Dataset Result
              </CardTitle>
            </CardHeader>
            <CardContent className="p-0">
              <div className="overflow-x-auto">
                <table className="w-full text-left text-sm">
                  <thead className="bg-slate-950/80 text-xs font-semibold text-slate-400 uppercase tracking-wider border-b border-slate-800">
                    <tr>
                      {result.columns.map((col) => (
                        <th key={col} className="px-4 py-3">
                          {col}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/60">
                    {result.rows.length === 0 ? (
                      <tr>
                        <td colSpan={result.columns.length} className="px-4 py-8 text-center text-slate-500">
                          No matching records returned.
                        </td>
                      </tr>
                    ) : (
                      result.rows.map((row, idx) => (
                        <tr key={idx} className="hover:bg-slate-800/30 transition-colors">
                          {result.columns.map((col) => {
                            const val = row[col];
                            return (
                              <td key={col} className="px-4 py-3 text-slate-300 font-mono text-xs">
                                {val !== null && val !== undefined ? String(val) : <span className="text-slate-600">null</span>}
                              </td>
                            );
                          })}
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </div>
            </CardContent>
          </Card>

          {/* Provenance Card */}
          {result.provenance && (
            <div className="p-3.5 rounded-lg bg-slate-950/60 border border-slate-800/60 text-xs text-slate-400 flex flex-wrap items-center justify-between gap-2">
              <div className="flex items-center gap-2">
                <Activity className="w-3.5 h-3.5 text-teal-400" />
                <span>Deterministic Provenance:</span>
                <span className="font-mono text-[11px] text-slate-300">
                  Version {result.provenance.dataset_version_id.slice(0, 8)}... | Tool v{result.provenance.tool_version}
                </span>
              </div>
              <span className="text-[11px] text-slate-500">{result.provenance.timestamp}</span>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
