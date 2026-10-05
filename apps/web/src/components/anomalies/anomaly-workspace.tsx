"use client";

import React, { useState, useEffect } from "react";
import {
  AnomalyDetectionRequest,
  AnomalyDetectionResponse,
  AnomalyPoint,
  AnomalySeverity,
  AnomalyStatus,
  Dataset,
  DetectionMethod,
  InsightResponse,
  RootCauseContributor,
} from "@/types";
import {
  Activity,
  AlertCircle,
  AlertTriangle,
  ArrowDownRight,
  ArrowUpRight,
  BarChart3,
  Check,
  CheckCircle2,
  ChevronRight,
  Clock,
  Eye,
  Filter,
  Layers,
  RefreshCw,
  Search,
  ShieldCheck,
  Sparkles,
  Table as TableIcon,
  ThumbsDown,
  ThumbsUp,
  TrendingDown,
  TrendingUp,
  X,
  Zap,
} from "lucide-react";

interface AnomalyWorkspaceProps {
  dataset?: Dataset;
  datasets?: Dataset[];
  token?: string;
  onAnomalyDetected?: (response: AnomalyDetectionResponse) => void;
}

export const AnomalyWorkspace: React.FC<AnomalyWorkspaceProps> = ({
  dataset: initialDataset,
  datasets = [],
  token,
  onAnomalyDetected,
}) => {
  const [selectedDatasetId, setSelectedDatasetId] = useState<string>(
    initialDataset?.id || (datasets.length > 0 ? datasets[0].id : "")
  );
  const [selectedMetric, setSelectedMetric] = useState<string>("");
  const [selectedTimeField, setSelectedTimeField] = useState<string>("");
  const [selectedDimension, setSelectedDimension] = useState<string>("");
  const [method, setMethod] = useState<DetectionMethod>("ROBUST_Z_SCORE");
  const [sensitivity, setSensitivity] = useState<number>(3.0);
  const [minSeverity, setMinSeverity] = useState<AnomalySeverity>("LOW");

  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [progressStep, setProgressStep] = useState<string>("");
  const [result, setResult] = useState<AnomalyDetectionResponse | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [selectedAnomaly, setSelectedAnomaly] = useState<AnomalyPoint | null>(null);
  const [viewMode, setViewMode] = useState<"insights" | "chart" | "table">("insights");
  const [statusFilter, setStatusFilter] = useState<string>("ALL");
  const [feedbackSuccess, setFeedbackSuccess] = useState<string | null>(null);

  const currentDataset = initialDataset || datasets.find((d) => d.id === selectedDatasetId);

  useEffect(() => {
    if (initialDataset?.id) {
      setSelectedDatasetId(initialDataset.id);
    }
  }, [initialDataset]);

  const handleRunDetection = async () => {
    if (!selectedDatasetId || !selectedMetric) {
      setErrorMessage("Please select a target numeric metric to analyze.");
      return;
    }

    setIsLoading(true);
    setErrorMessage(null);
    setProgressStep("Establishing deterministic statistical baseline…");

    try {
      setTimeout(() => setProgressStep("Calculating dispersion & robust score bounds…"), 400);
      setTimeout(() => setProgressStep("Evaluating materiality & anti-fatigue weights…"), 800);
      setTimeout(() => setProgressStep("Decomposing dimensional root-cause contributors…"), 1200);

      const payload: AnomalyDetectionRequest = {
        dataset_id: selectedDatasetId,
        metric_fields: [selectedMetric],
        time_field: selectedTimeField || null,
        dimension_fields: selectedDimension ? [selectedDimension] : undefined,
        method: method,
        sensitivity: sensitivity,
        min_severity: minSeverity,
      };

      const res = await fetch("/api/v1/anomalies/detect", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        body: JSON.stringify(payload),
      });

      if (!res.ok) {
        const errData = await res.json().catch(() => ({}));
        throw new Error(errData.detail || `Detection failed with HTTP status ${res.status}`);
      }

      const data: AnomalyDetectionResponse = await res.json();
      setResult(data);
      if (data.anomalies.length > 0) {
        setSelectedAnomaly(data.anomalies[0]);
      }
      if (onAnomalyDetected) {
        onAnomalyDetected(data);
      }
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to execute anomaly detection.";
      setErrorMessage(msg);
    } finally {
      setIsLoading(false);
      setProgressStep("");
    }
  };

  const handleStatusUpdate = async (anomalyId: string, newStatus: AnomalyStatus) => {
    try {
      const res = await fetch(`/api/v1/anomalies/${anomalyId}/status`, {
        method: "PATCH",
        headers: {
          "Content-Type": "application/json",
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        body: JSON.stringify({ status: newStatus }),
      });

      if (res.ok) {
        const updatedPoint: AnomalyPoint = await res.json();
        if (result) {
          const updatedList = result.anomalies.map((a) => (a.id === anomalyId ? updatedPoint : a));
          setResult({ ...result, anomalies: updatedList });
        }
        if (selectedAnomaly?.id === anomalyId) {
          setSelectedAnomaly(updatedPoint);
        }
      }
    } catch (err) {
      console.error("Failed to update anomaly status", err);
    }
  };

  const handleInsightFeedback = async (insightId: string, feedback: string) => {
    try {
      const res = await fetch(`/api/v1/insights/${insightId}/feedback`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        body: JSON.stringify({ feedback }),
      });

      if (res.ok) {
        setFeedbackSuccess(insightId);
        setTimeout(() => setFeedbackSuccess(null), 2500);
      }
    } catch (err) {
      console.error("Failed to submit feedback", err);
    }
  };

  const getSeverityBadgeClass = (severity: AnomalySeverity) => {
    switch (severity) {
      case "CRITICAL":
        return "bg-rose-500/15 text-rose-400 border border-rose-500/30";
      case "HIGH":
        return "bg-amber-500/15 text-amber-400 border border-amber-500/30";
      case "MEDIUM":
        return "bg-yellow-500/15 text-yellow-300 border border-yellow-500/30";
      case "LOW":
        return "bg-sky-500/15 text-sky-400 border border-sky-500/30";
      default:
        return "bg-slate-500/15 text-slate-400 border border-slate-500/30";
    }
  };

  const filteredAnomalies = result?.anomalies.filter((a) => {
    if (statusFilter === "ALL") return true;
    return a.status === statusFilter;
  }) || [];

  return (
    <div className="space-y-6">
      {/* 1. Header & Quick Metrics */}
      <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4 bg-slate-900/60 p-6 rounded-2xl border border-slate-800/80 backdrop-blur-xl">
        <div>
          <div className="flex items-center gap-2.5">
            <div className="p-2 rounded-xl bg-gradient-to-br from-rose-500/20 to-amber-500/20 border border-rose-500/30 text-rose-400">
              <Zap className="w-5 h-5" />
            </div>
            <h1 className="text-xl font-semibold text-white tracking-tight">
              Anomaly Intelligence & Proactive Insights
            </h1>
          </div>
          <p className="text-sm text-slate-400 mt-1 max-w-2xl">
            Deterministic statistical detection, materiality scoring, and explainable dimensional root-cause analysis with zero AI hallucinations.
          </p>
        </div>

        {result && (
          <div className="flex items-center gap-2 flex-wrap">
            <div className="px-3 py-1.5 rounded-lg bg-slate-800/80 border border-slate-700/60 text-xs text-slate-300">
              Total: <span className="font-semibold text-white">{result.total_anomalies_count}</span>
            </div>
            {result.critical_count > 0 && (
              <div className="px-3 py-1.5 rounded-lg bg-rose-500/15 border border-rose-500/30 text-xs text-rose-300 font-medium">
                {result.critical_count} Critical
              </div>
            )}
            {result.high_count > 0 && (
              <div className="px-3 py-1.5 rounded-lg bg-amber-500/15 border border-amber-500/30 text-xs text-amber-300 font-medium">
                {result.high_count} High
              </div>
            )}
            {result.medium_count > 0 && (
              <div className="px-3 py-1.5 rounded-lg bg-yellow-500/15 border border-yellow-500/30 text-xs text-yellow-300 font-medium">
                {result.medium_count} Medium
              </div>
            )}
            <div className="px-3 py-1.5 rounded-lg bg-slate-800/50 border border-slate-700/40 text-xs text-slate-400 flex items-center gap-1">
              <Clock className="w-3.5 h-3.5" />
              {result.execution_time_ms.toFixed(1)}ms
            </div>
          </div>
        )}
      </div>

      {/* 2. Configuration & Parameter Panel */}
      <div className="bg-slate-900/40 p-6 rounded-2xl border border-slate-800/60 space-y-4">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {/* Dataset Selector */}
          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1.5">Dataset</label>
            <select
              value={selectedDatasetId}
              onChange={(e) => setSelectedDatasetId(e.target.value)}
              className="w-full bg-slate-800/90 border border-slate-700/80 rounded-xl px-3.5 py-2 text-sm text-white focus:outline-none focus:ring-2 focus:ring-sky-500/40 transition-all"
            >
              {datasets.map((d) => (
                <option key={d.id} value={d.id}>
                  {d.name}
                </option>
              ))}
            </select>
          </div>

          {/* Metric Field */}
          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1.5">Numeric Measure</label>
            <input
              type="text"
              placeholder="e.g. revenue, orders, volume"
              value={selectedMetric}
              onChange={(e) => setSelectedMetric(e.target.value)}
              className="w-full bg-slate-800/90 border border-slate-700/80 rounded-xl px-3.5 py-2 text-sm text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-sky-500/40 transition-all"
            />
          </div>

          {/* Time Field */}
          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1.5">Time Column (Optional)</label>
            <input
              type="text"
              placeholder="e.g. order_date, timestamp"
              value={selectedTimeField}
              onChange={(e) => setSelectedTimeField(e.target.value)}
              className="w-full bg-slate-800/90 border border-slate-700/80 rounded-xl px-3.5 py-2 text-sm text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-sky-500/40 transition-all"
            />
          </div>

          {/* Root-Cause Dimension */}
          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1.5">Decomposition Dimension</label>
            <input
              type="text"
              placeholder="e.g. region, category, channel"
              value={selectedDimension}
              onChange={(e) => setSelectedDimension(e.target.value)}
              className="w-full bg-slate-800/90 border border-slate-700/80 rounded-xl px-3.5 py-2 text-sm text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-sky-500/40 transition-all"
            />
          </div>
        </div>

        {/* Method & Sensitivity Row */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 pt-2 border-t border-slate-800/40">
          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1.5">Statistical Detector</label>
            <select
              value={method}
              onChange={(e) => setMethod(e.target.value as DetectionMethod)}
              className="w-full bg-slate-800/90 border border-slate-700/80 rounded-xl px-3.5 py-2 text-sm text-white focus:outline-none focus:ring-2 focus:ring-sky-500/40"
            >
              <option value="ROBUST_Z_SCORE">Robust Z-Score (Median / MAD - Recommended)</option>
              <option value="Z_SCORE">Standard Z-Score (Mean / Std)</option>
              <option value="IQR">Interquartile Range (Tukey Fences)</option>
              <option value="ROLLING_BASELINE">Rolling Dynamic Moving Baseline</option>
              <option value="SEASONAL_BASELINE">Seasonal Cycle Baseline</option>
              <option value="FORECAST_DEVIATION">Forecast Interval Deviation</option>
            </select>
          </div>

          <div>
            <div className="flex justify-between items-center mb-1.5">
              <label className="text-xs font-medium text-slate-300">Sensitivity Multiplier</label>
              <span className="text-xs text-slate-400 font-mono">{sensitivity.toFixed(1)}σ</span>
            </div>
            <input
              type="range"
              min={1.0}
              max={6.0}
              step={0.1}
              value={sensitivity}
              onChange={(e) => setSensitivity(parseFloat(e.target.value))}
              className="w-full accent-sky-500 cursor-pointer"
            />
          </div>

          <div className="flex items-end">
            <button
              onClick={handleRunDetection}
              disabled={isLoading}
              className="w-full h-[38px] flex items-center justify-center gap-2 px-4 py-2 rounded-xl bg-gradient-to-r from-rose-500 via-amber-500 to-sky-500 hover:from-rose-600 hover:to-sky-600 text-white font-medium text-sm shadow-lg shadow-rose-500/10 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isLoading ? (
                <>
                  <RefreshCw className="w-4 h-4 animate-spin" />
                  <span>Analyzing…</span>
                </>
              ) : (
                <>
                  <Sparkles className="w-4 h-4" />
                  <span>Detect Anomalies & Insights</span>
                </>
              )}
            </button>
          </div>
        </div>

        {/* Progress or Error Banner */}
        {isLoading && progressStep && (
          <div className="flex items-center gap-2.5 text-xs text-sky-400 bg-sky-500/10 border border-sky-500/20 p-3 rounded-xl animate-pulse">
            <RefreshCw className="w-3.5 h-3.5 animate-spin" />
            <span>{progressStep}</span>
          </div>
        )}

        {errorMessage && (
          <div className="flex items-center gap-2.5 text-xs text-rose-400 bg-rose-500/10 border border-rose-500/20 p-3 rounded-xl">
            <AlertCircle className="w-4 h-4 flex-shrink-0" />
            <span>{errorMessage}</span>
          </div>
        )}
      </div>

      {/* 3. Main Results Display */}
      {result && (
        <div className="space-y-6">
          {/* View Mode Toggle & Status Filter */}
          <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 bg-slate-900/40 p-3 rounded-xl border border-slate-800/60">
            <div className="flex items-center gap-1.5">
              <button
                onClick={() => setViewMode("insights")}
                className={`flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg text-xs font-medium transition-all ${
                  viewMode === "insights"
                    ? "bg-sky-500 text-white shadow-md shadow-sky-500/20"
                    : "text-slate-400 hover:text-white hover:bg-slate-800/60"
                }`}
              >
                <Sparkles className="w-3.5 h-3.5" />
                Proactive Feed ({result.insights.length})
              </button>
              <button
                onClick={() => setViewMode("chart")}
                className={`flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg text-xs font-medium transition-all ${
                  viewMode === "chart"
                    ? "bg-sky-500 text-white shadow-md shadow-sky-500/20"
                    : "text-slate-400 hover:text-white hover:bg-slate-800/60"
                }`}
              >
                <BarChart3 className="w-3.5 h-3.5" />
                Timeline & Breakdown
              </button>
              <button
                onClick={() => setViewMode("table")}
                className={`flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg text-xs font-medium transition-all ${
                  viewMode === "table"
                    ? "bg-sky-500 text-white shadow-md shadow-sky-500/20"
                    : "text-slate-400 hover:text-white hover:bg-slate-800/60"
                }`}
              >
                <TableIcon className="w-3.5 h-3.5" />
                Evidence Table ({result.anomalies.length})
              </button>
            </div>

            <div className="flex items-center gap-2">
              <span className="text-xs text-slate-400 flex items-center gap-1">
                <Filter className="w-3 h-3" /> Status:
              </span>
              <select
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value)}
                className="bg-slate-800/90 border border-slate-700/70 rounded-lg px-2.5 py-1 text-xs text-white focus:outline-none"
              >
                <option value="ALL">All Alerts</option>
                <option value="DETECTED">Detected</option>
                <option value="ACKNOWLEDGED">Acknowledged</option>
                <option value="RESOLVED">Resolved</option>
                <option value="DISMISSED">Dismissed</option>
              </select>
            </div>
          </div>

          {/* VIEW: Proactive Feed */}
          {viewMode === "insights" && (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {result.insights.length === 0 ? (
                <div className="col-span-2 text-center py-12 bg-slate-900/30 rounded-2xl border border-slate-800/50">
                  <CheckCircle2 className="w-8 h-8 text-emerald-400 mx-auto mb-2" />
                  <p className="text-sm text-slate-300 font-medium">No anomalous deviations detected</p>
                  <p className="text-xs text-slate-500 mt-0.5">Metrics are tracking within normal statistical tolerance.</p>
                </div>
              ) : (
                result.insights.map((insight) => (
                  <div
                    key={insight.id}
                    className="p-5 rounded-2xl bg-slate-900/50 border border-slate-800/80 hover:border-slate-700/80 transition-all flex flex-col justify-between space-y-3"
                  >
                    <div>
                      <div className="flex items-center justify-between gap-2 mb-2">
                        <span className={`px-2.5 py-0.5 rounded-md text-[11px] font-semibold tracking-wide ${getSeverityBadgeClass(insight.severity)}`}>
                          {insight.severity}
                        </span>
                        <span className="text-[11px] text-slate-500 font-mono">
                          {new Date(insight.created_at).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
                        </span>
                      </div>
                      <h3 className="text-sm font-semibold text-white">{insight.title}</h3>
                      <p className="text-xs text-slate-300 mt-1 leading-relaxed">{insight.summary}</p>
                    </div>

                    <div className="pt-3 border-t border-slate-800/60 flex items-center justify-between text-xs">
                      <div className="flex items-center gap-1.5 text-slate-400">
                        <span>Feedback:</span>
                        <button
                          onClick={() => handleInsightFeedback(insight.id, "useful")}
                          className="p-1 hover:text-emerald-400 hover:bg-slate-800 rounded transition-colors"
                          title="Helpful insight"
                        >
                          <ThumbsUp className="w-3.5 h-3.5" />
                        </button>
                        <button
                          onClick={() => handleInsightFeedback(insight.id, "not_useful")}
                          className="p-1 hover:text-rose-400 hover:bg-slate-800 rounded transition-colors"
                          title="Not useful"
                        >
                          <ThumbsDown className="w-3.5 h-3.5" />
                        </button>
                        {feedbackSuccess === insight.id && (
                          <span className="text-[10px] text-emerald-400 font-medium ml-1">Feedback saved!</span>
                        )}
                      </div>

                      {insight.anomaly_id && (
                        <button
                          onClick={() => {
                            const anom = result.anomalies.find((a) => a.id === insight.anomaly_id);
                            if (anom) setSelectedAnomaly(anom);
                            setViewMode("chart");
                          }}
                          className="text-xs text-sky-400 hover:text-sky-300 font-medium flex items-center gap-1"
                        >
                          Inspect Evidence <ChevronRight className="w-3 h-3" />
                        </button>
                      )}
                    </div>
                  </div>
                ))
              )}
            </div>
          )}

          {/* VIEW: Chart & Root Cause Breakdown */}
          {viewMode === "chart" && (
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              {/* Left Column: Anomalies list selector */}
              <div className="lg:col-span-1 space-y-3">
                <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Detected Anomaly Points</h3>
                <div className="space-y-2 max-h-[520px] overflow-y-auto pr-1">
                  {filteredAnomalies.map((anom) => {
                    const isSelected = selectedAnomaly?.id === anom.id;
                    const isNegative = anom.deviation < 0;
                    return (
                      <div
                        key={anom.id}
                        onClick={() => setSelectedAnomaly(anom)}
                        className={`p-3.5 rounded-xl border cursor-pointer transition-all ${
                          isSelected
                            ? "bg-slate-800/90 border-sky-500/60 shadow-lg shadow-sky-500/10"
                            : "bg-slate-900/40 border-slate-800/70 hover:border-slate-700/80"
                        }`}
                      >
                        <div className="flex items-center justify-between gap-2">
                          <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${getSeverityBadgeClass(anom.severity)}`}>
                            {anom.severity}
                          </span>
                          <span className="text-xs text-slate-400 font-mono">{anom.period}</span>
                        </div>
                        <div className="flex items-baseline justify-between mt-2">
                          <span className="text-sm font-semibold text-white">
                            {anom.observed_value.toLocaleString()}
                          </span>
                          <span className={`text-xs font-medium flex items-center gap-0.5 ${isNegative ? "text-rose-400" : "text-emerald-400"}`}>
                            {isNegative ? <TrendingDown className="w-3 h-3" /> : <TrendingUp className="w-3 h-3" />}
                            {anom.deviation_pct > 0 ? `+${anom.deviation_pct}%` : `${anom.deviation_pct}%`}
                          </span>
                        </div>
                        <div className="text-[11px] text-slate-500 mt-1 flex items-center justify-between">
                          <span>Expected: {anom.expected_value.toLocaleString()}</span>
                          <span className="font-mono">Score: {anom.anomaly_score.toFixed(1)}</span>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>

              {/* Right Column: Selected Anomaly Detail & Root Cause Breakdown */}
              <div className="lg:col-span-2 space-y-4">
                {selectedAnomaly ? (
                  <div className="bg-slate-900/50 p-6 rounded-2xl border border-slate-800/80 space-y-6">
                    {/* Detail Header */}
                    <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-4 border-b border-slate-800/60">
                      <div>
                        <div className="flex items-center gap-2">
                          <span className={`px-2.5 py-0.5 rounded-md text-xs font-bold ${getSeverityBadgeClass(selectedAnomaly.severity)}`}>
                            {selectedAnomaly.severity}
                          </span>
                          <h2 className="text-base font-semibold text-white">
                            {selectedAnomaly.metric_field} ({selectedAnomaly.period})
                          </h2>
                        </div>
                        <p className="text-xs text-slate-400 mt-1">
                          Detected via <span className="font-medium text-slate-300">{selectedAnomaly.detection_method}</span> · Score: {selectedAnomaly.anomaly_score.toFixed(2)}
                        </p>
                      </div>

                      <div className="flex items-center gap-2">
                        {selectedAnomaly.status !== "ACKNOWLEDGED" && (
                          <button
                            onClick={() => handleStatusUpdate(selectedAnomaly.id, "ACKNOWLEDGED")}
                            className="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-medium transition-colors"
                          >
                            Acknowledge
                          </button>
                        )}
                        {selectedAnomaly.status !== "RESOLVED" && (
                          <button
                            onClick={() => handleStatusUpdate(selectedAnomaly.id, "RESOLVED")}
                            className="px-3 py-1.5 rounded-lg bg-emerald-500/20 hover:bg-emerald-500/30 text-emerald-300 border border-emerald-500/30 text-xs font-medium transition-colors"
                          >
                            Mark Resolved
                          </button>
                        )}
                        {selectedAnomaly.status !== "DISMISSED" && (
                          <button
                            onClick={() => handleStatusUpdate(selectedAnomaly.id, "DISMISSED")}
                            className="px-3 py-1.5 rounded-lg bg-slate-800/40 hover:bg-slate-800 text-slate-400 text-xs transition-colors"
                          >
                            Dismiss
                          </button>
                        )}
                      </div>
                    </div>

                    {/* Metric Cards Comparison */}
                    <div className="grid grid-cols-3 gap-3">
                      <div className="bg-slate-800/50 p-3.5 rounded-xl border border-slate-700/40">
                        <span className="text-[11px] text-slate-400 block">Observed Value</span>
                        <span className="text-base font-semibold text-white mt-0.5 block">
                          {selectedAnomaly.observed_value.toLocaleString()}
                        </span>
                      </div>
                      <div className="bg-slate-800/50 p-3.5 rounded-xl border border-slate-700/40">
                        <span className="text-[11px] text-slate-400 block">Baseline Expected</span>
                        <span className="text-base font-semibold text-slate-300 mt-0.5 block">
                          {selectedAnomaly.expected_value.toLocaleString()}
                        </span>
                      </div>
                      <div className="bg-slate-800/50 p-3.5 rounded-xl border border-slate-700/40">
                        <span className="text-[11px] text-slate-400 block">Deviation Delta</span>
                        <span className={`text-base font-semibold mt-0.5 block ${selectedAnomaly.deviation < 0 ? "text-rose-400" : "text-emerald-400"}`}>
                          {selectedAnomaly.deviation > 0 ? `+${selectedAnomaly.deviation.toLocaleString()}` : selectedAnomaly.deviation.toLocaleString()} ({selectedAnomaly.deviation_pct}%)
                        </span>
                      </div>
                    </div>

                    {/* Root Cause Subgroup Breakdown */}
                    <div className="space-y-3">
                      <div className="flex items-center justify-between">
                        <h4 className="text-xs font-semibold text-slate-300 uppercase tracking-wider">
                          Dimensional Breakdown (Top Contributors)
                        </h4>
                        <span className="text-[11px] text-slate-500 italic">Non-causal variance contribution</span>
                      </div>

                      {selectedAnomaly.root_causes.length === 0 ? (
                        <div className="text-xs text-slate-500 bg-slate-800/30 p-4 rounded-xl text-center">
                          No categorical dimension was specified for root-cause decomposition.
                        </div>
                      ) : (
                        <div className="space-y-2.5">
                          {selectedAnomaly.root_causes.map((rc, idx) => (
                            <div key={idx} className="bg-slate-800/40 p-3 rounded-xl border border-slate-700/40 space-y-1.5">
                              <div className="flex items-center justify-between text-xs">
                                <span className="font-semibold text-white">
                                  {rc.dimension_field}: <span className="text-sky-400">{rc.dimension_value}</span>
                                </span>
                                <span className="font-mono text-slate-300">{rc.contribution_pct}% contribution</span>
                              </div>
                              <div className="w-full h-1.5 bg-slate-700/60 rounded-full overflow-hidden">
                                <div
                                  className="h-full bg-gradient-to-r from-sky-500 to-amber-500 rounded-full"
                                  style={{ width: `${Math.min(100, rc.contribution_pct)}%` }}
                                />
                              </div>
                              <p className="text-[11px] text-slate-400 italic">{rc.narrative}</p>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  </div>
                ) : (
                  <div className="text-center py-20 bg-slate-900/30 rounded-2xl border border-slate-800/50">
                    <p className="text-sm text-slate-400">Select an anomaly point to view details</p>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* VIEW: Table Evidence Fallback */}
          {viewMode === "table" && (
            <div className="bg-slate-900/50 rounded-2xl border border-slate-800/80 overflow-hidden">
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs text-slate-300">
                  <thead className="bg-slate-800/60 text-slate-400 border-b border-slate-700/60 font-medium">
                    <tr>
                      <th className="px-4 py-3">Severity</th>
                      <th className="px-4 py-3">Period</th>
                      <th className="px-4 py-3">Metric</th>
                      <th className="px-4 py-3">Observed</th>
                      <th className="px-4 py-3">Expected</th>
                      <th className="px-4 py-3">Deviation</th>
                      <th className="px-4 py-3">Score</th>
                      <th className="px-4 py-3">Method</th>
                      <th className="px-4 py-3">Status</th>
                      <th className="px-4 py-3 text-right">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/60">
                    {filteredAnomalies.map((a) => (
                      <tr key={a.id} className="hover:bg-slate-800/40 transition-colors">
                        <td className="px-4 py-3">
                          <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${getSeverityBadgeClass(a.severity)}`}>
                            {a.severity}
                          </span>
                        </td>
                        <td className="px-4 py-3 font-mono text-white">{a.period}</td>
                        <td className="px-4 py-3 font-medium text-slate-200">{a.metric_field}</td>
                        <td className="px-4 py-3 font-mono text-white">{a.observed_value.toLocaleString()}</td>
                        <td className="px-4 py-3 font-mono text-slate-400">{a.expected_value.toLocaleString()}</td>
                        <td className="px-4 py-3 font-mono">
                          <span className={a.deviation < 0 ? "text-rose-400" : "text-emerald-400"}>
                            {a.deviation > 0 ? `+${a.deviation.toLocaleString()}` : a.deviation.toLocaleString()} ({a.deviation_pct}%)
                          </span>
                        </td>
                        <td className="px-4 py-3 font-mono">{a.anomaly_score.toFixed(2)}</td>
                        <td className="px-4 py-3 text-slate-400">{a.detection_method}</td>
                        <td className="px-4 py-3">
                          <span className="text-slate-300">{a.status}</span>
                        </td>
                        <td className="px-4 py-3 text-right">
                          <button
                            onClick={() => {
                              setSelectedAnomaly(a);
                              setViewMode("chart");
                            }}
                            className="text-sky-400 hover:text-sky-300 font-medium"
                          >
                            Inspect
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
