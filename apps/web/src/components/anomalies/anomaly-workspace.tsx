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
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { PageHero } from "@/components/ui/page-hero";

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

  const getSeverityBadgeVariant = (severity: AnomalySeverity): "danger" | "amber" | "blue" | "outline" => {
    switch (severity) {
      case "CRITICAL":
        return "danger";
      case "HIGH":
        return "amber";
      case "MEDIUM":
        return "blue";
      case "LOW":
        return "outline";
      default:
        return "outline";
    }
  };

  const filteredAnomalies = result?.anomalies.filter((a) => {
    if (statusFilter === "ALL") return true;
    return a.status === statusFilter;
  }) || [];

  return (
    <div className="space-y-6">
      {/* 1. Header Banner via Shared PageHero */}
      <PageHero
        variant="gradient"
        phaseBadge="Phase 10 Active"
        subtitle="Deterministic Statistical Detection & Root-Cause"
        icon={<Zap className="w-5 h-5" />}
        title="Anomaly Intelligence & Proactive Insights"
        description="Deterministic statistical detection, materiality scoring, and explainable dimensional root-cause analysis with zero AI hallucinations."
        statusBadge={
          <>
            <ShieldCheck className="w-4 h-4 text-teal-300 shrink-0" />
            <span>Zero Hallucination Scoring</span>
          </>
        }
        actions={
          result ? (
            <div className="flex items-center gap-2 flex-wrap">
              <div className="px-3 py-1.5 rounded-xl bg-white/10 backdrop-blur border border-white/15 text-xs text-white font-medium">
                Total: <span className="font-bold text-white font-mono">{result.total_anomalies_count}</span>
              </div>
              {result.critical_count > 0 && (
                <span className="px-2.5 py-1 rounded-xl bg-rose/20 text-rose-300 border border-rose-400/30 text-xs font-semibold">
                  {result.critical_count} Critical
                </span>
              )}
              {result.high_count > 0 && (
                <span className="px-2.5 py-1 rounded-xl bg-amber/20 text-amber-300 border border-amber-400/30 text-xs font-semibold">
                  {result.high_count} High
                </span>
              )}
              {result.medium_count > 0 && (
                <span className="px-2.5 py-1 rounded-xl bg-blue/20 text-blue-300 border border-blue-400/30 text-xs font-semibold">
                  {result.medium_count} Medium
                </span>
              )}
              <div className="px-3 py-1.5 rounded-xl bg-white/10 border border-white/15 text-xs text-teal-100 flex items-center gap-1">
                <Clock className="w-3.5 h-3.5 text-teal-300" />
                {result.execution_time_ms.toFixed(1)}ms
              </div>
            </div>
          ) : undefined
        }
      />

      {/* 2. Configuration & Parameter Panel */}
      <div className="bg-surface p-6 rounded-2xl border border-border shadow-soft space-y-4">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {/* Dataset Selector */}
          <div>
            <label className="block text-xs font-medium text-slate mb-1.5">Dataset</label>
            <select
              value={selectedDatasetId}
              onChange={(e) => setSelectedDatasetId(e.target.value)}
              className="w-full bg-surface border border-border rounded-xl px-3.5 py-2 text-sm text-ink focus:outline-none focus:ring-2 focus:ring-teal"
            >
              {datasets.length === 0 ? (
                <option value="" disabled className="text-slate-400 bg-white">No datasets available</option>
              ) : (
                datasets.map((d) => (
                  <option key={d.id} value={d.id} className="text-slate-800 bg-white font-medium">
                    {d.name}
                  </option>
                ))
              )}
            </select>
          </div>

          {/* Metric Field */}
          <div>
            <label className="block text-xs font-medium text-slate mb-1.5">Numeric Measure</label>
            <input
              type="text"
              placeholder="e.g. revenue, orders, volume"
              value={selectedMetric}
              onChange={(e) => setSelectedMetric(e.target.value)}
              className="w-full bg-surface border border-border rounded-xl px-3.5 py-2 text-sm text-ink placeholder-slate focus:outline-none focus:ring-2 focus:ring-teal"
            />
          </div>

          {/* Time Field */}
          <div>
            <label className="block text-xs font-medium text-slate mb-1.5">Time Column (Optional)</label>
            <input
              type="text"
              placeholder="e.g. order_date, timestamp"
              value={selectedTimeField}
              onChange={(e) => setSelectedTimeField(e.target.value)}
              className="w-full bg-surface border border-border rounded-xl px-3.5 py-2 text-sm text-ink placeholder-slate focus:outline-none focus:ring-2 focus:ring-teal"
            />
          </div>

          {/* Root-Cause Dimension */}
          <div>
            <label className="block text-xs font-medium text-slate mb-1.5">Decomposition Dimension</label>
            <input
              type="text"
              placeholder="e.g. region, category, channel"
              value={selectedDimension}
              onChange={(e) => setSelectedDimension(e.target.value)}
              className="w-full bg-surface border border-border rounded-xl px-3.5 py-2 text-sm text-ink placeholder-slate focus:outline-none focus:ring-2 focus:ring-teal"
            />
          </div>
        </div>

        {/* Method & Sensitivity Row */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 pt-4 border-t border-border">
          <div>
            <label className="block text-xs font-medium text-slate mb-1.5">Statistical Detector</label>
            <select
              value={method}
              onChange={(e) => setMethod(e.target.value as DetectionMethod)}
              className="w-full bg-surface border border-border rounded-xl px-3.5 py-2 text-sm text-ink focus:outline-none focus:ring-2 focus:ring-teal"
            >
              <option value="ROBUST_Z_SCORE" className="text-slate-800 bg-white font-medium">Robust Z-Score (Median / MAD - Recommended)</option>
              <option value="Z_SCORE" className="text-slate-800 bg-white font-medium">Standard Z-Score (Mean / Std)</option>
              <option value="IQR" className="text-slate-800 bg-white font-medium">Interquartile Range (Tukey Fences)</option>
              <option value="ROLLING_BASELINE" className="text-slate-800 bg-white font-medium">Rolling Dynamic Moving Baseline</option>
              <option value="SEASONAL_BASELINE" className="text-slate-800 bg-white font-medium">Seasonal Cycle Baseline</option>
              <option value="FORECAST_DEVIATION" className="text-slate-800 bg-white font-medium">Forecast Interval Deviation</option>
            </select>
          </div>

          <div>
            <div className="flex justify-between items-center mb-1.5">
              <label className="text-xs font-medium text-slate">Sensitivity Multiplier</label>
              <span className="text-xs text-ink font-mono font-semibold">{sensitivity.toFixed(1)}σ</span>
            </div>
            <input
              type="range"
              min={1.0}
              max={6.0}
              step={0.1}
              value={sensitivity}
              onChange={(e) => setSensitivity(parseFloat(e.target.value))}
              className="w-full accent-teal cursor-pointer"
            />
          </div>

          <div className="flex items-end">
            <Button
              onClick={handleRunDetection}
              disabled={isLoading}
              isLoading={isLoading}
              variant="primary"
              className="w-full"
              leftIcon={<Sparkles className="w-4 h-4" />}
            >
              Detect Anomalies & Insights
            </Button>
          </div>
        </div>

        {/* Progress or Error Banner */}
        {isLoading && progressStep && (
          <div className="flex items-center gap-2.5 text-xs text-teal bg-teal-soft border border-teal-border p-3 rounded-xl">
            <RefreshCw className="w-3.5 h-3.5 animate-spin" />
            <span>{progressStep}</span>
          </div>
        )}

        {errorMessage && (
          <div className="flex items-center gap-2.5 text-xs text-danger bg-danger/10 border border-danger/20 p-3 rounded-xl">
            <AlertCircle className="w-4 h-4 flex-shrink-0" />
            <span>{errorMessage}</span>
          </div>
        )}
      </div>

      {/* 3. Main Results Display */}
      {result && (
        <div className="space-y-6">
          {/* View Mode Toggle & Status Filter */}
          <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 bg-surface p-3 rounded-2xl border border-border shadow-soft">
            <div className="flex items-center gap-1.5">
              <Button
                variant={viewMode === "insights" ? "primary" : "ghost"}
                size="sm"
                onClick={() => setViewMode("insights")}
                leftIcon={<Sparkles className="w-3.5 h-3.5" />}
              >
                Proactive Feed ({result.insights.length})
              </Button>
              <Button
                variant={viewMode === "chart" ? "primary" : "ghost"}
                size="sm"
                onClick={() => setViewMode("chart")}
                leftIcon={<BarChart3 className="w-3.5 h-3.5" />}
              >
                Timeline & Breakdown
              </Button>
              <Button
                variant={viewMode === "table" ? "primary" : "ghost"}
                size="sm"
                onClick={() => setViewMode("table")}
                leftIcon={<TableIcon className="w-3.5 h-3.5" />}
              >
                Evidence Table ({result.anomalies.length})
              </Button>
            </div>

            <div className="flex items-center gap-2">
              <span className="text-xs text-slate flex items-center gap-1">
                <Filter className="w-3 h-3" /> Status:
              </span>
              <select
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value)}
                className="bg-surface border border-border rounded-xl px-2.5 py-1 text-xs text-ink focus:outline-none"
              >
                <option value="ALL" className="text-slate-800 bg-white font-medium">All Alerts</option>
                <option value="DETECTED" className="text-slate-800 bg-white font-medium">Detected</option>
                <option value="ACKNOWLEDGED" className="text-slate-800 bg-white font-medium">Acknowledged</option>
                <option value="RESOLVED" className="text-slate-800 bg-white font-medium">Resolved</option>
                <option value="DISMISSED" className="text-slate-800 bg-white font-medium">Dismissed</option>
              </select>
            </div>
          </div>

          {/* VIEW: Proactive Feed */}
          {viewMode === "insights" && (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {result.insights.length === 0 ? (
                <div className="col-span-2 text-center py-12 bg-surface rounded-2xl border border-border shadow-soft">
                  <CheckCircle2 className="w-8 h-8 text-teal mx-auto mb-2" />
                  <p className="text-sm text-ink font-semibold">No anomalous deviations detected</p>
                  <p className="text-xs text-slate mt-0.5">Metrics are tracking within normal statistical tolerance.</p>
                </div>
              ) : (
                result.insights.map((insight) => (
                  <Card
                    key={insight.id}
                    className="p-5 bg-surface border-border shadow-soft flex flex-col justify-between space-y-3"
                  >
                    <div>
                      <div className="flex items-center justify-between gap-2 mb-2">
                        <Badge variant={getSeverityBadgeVariant(insight.severity)}>
                          {insight.severity}
                        </Badge>
                        <span className="text-[11px] text-slate font-mono">
                          {new Date(insight.created_at).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
                        </span>
                      </div>
                      <h3 className="text-sm font-bold text-ink">{insight.title}</h3>
                      <p className="text-xs text-slate mt-1 leading-relaxed">{insight.summary}</p>
                    </div>

                    <div className="pt-3 border-t border-border flex items-center justify-between text-xs">
                      <div className="flex items-center gap-1.5 text-slate">
                        <span>Feedback:</span>
                        <button
                          onClick={() => handleInsightFeedback(insight.id, "useful")}
                          className="p-1 hover:text-teal hover:bg-cloud rounded transition-colors"
                          title="Helpful insight"
                        >
                          <ThumbsUp className="w-3.5 h-3.5" />
                        </button>
                        <button
                          onClick={() => handleInsightFeedback(insight.id, "not_useful")}
                          className="p-1 hover:text-danger hover:bg-cloud rounded transition-colors"
                          title="Not useful"
                        >
                          <ThumbsDown className="w-3.5 h-3.5" />
                        </button>
                        {feedbackSuccess === insight.id && (
                          <span className="text-[10px] text-teal font-medium ml-1">Feedback saved!</span>
                        )}
                      </div>

                      {insight.anomaly_id && (
                        <button
                          onClick={() => {
                            const anom = result.anomalies.find((a) => a.id === insight.anomaly_id);
                            if (anom) setSelectedAnomaly(anom);
                            setViewMode("chart");
                          }}
                          className="text-xs text-teal hover:underline font-semibold flex items-center gap-1"
                        >
                          Inspect Evidence <ChevronRight className="w-3 h-3" />
                        </button>
                      )}
                    </div>
                  </Card>
                ))
              )}
            </div>
          )}

          {/* VIEW: Chart & Root Cause Breakdown */}
          {viewMode === "chart" && (
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              {/* Left Column: Anomalies list selector */}
              <div className="lg:col-span-1 space-y-3">
                <h3 className="text-xs font-semibold text-slate uppercase tracking-wider">Detected Anomaly Points</h3>
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
                            ? "bg-teal-soft/40 border-teal-border shadow-soft"
                            : "bg-surface border-border hover:bg-cloud-subtle"
                        }`}
                      >
                        <div className="flex items-center justify-between gap-2">
                          <Badge variant={getSeverityBadgeVariant(anom.severity)}>
                            {anom.severity}
                          </Badge>
                          <span className="text-xs text-slate font-mono">{anom.period}</span>
                        </div>
                        <div className="flex items-baseline justify-between mt-2">
                          <span className="text-sm font-bold text-ink">
                            {anom.observed_value.toLocaleString()}
                          </span>
                          <span className={`text-xs font-semibold flex items-center gap-0.5 ${isNegative ? "text-danger" : "text-teal"}`}>
                            {isNegative ? <TrendingDown className="w-3 h-3" /> : <TrendingUp className="w-3 h-3" />}
                            {anom.deviation_pct > 0 ? `+${anom.deviation_pct}%` : `${anom.deviation_pct}%`}
                          </span>
                        </div>
                        <div className="text-[11px] text-slate mt-1 flex items-center justify-between">
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
                  <Card className="bg-surface p-6 rounded-2xl border border-border shadow-soft space-y-6">
                    {/* Detail Header */}
                    <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-4 border-b border-border">
                      <div>
                        <div className="flex items-center gap-2">
                          <Badge variant={getSeverityBadgeVariant(selectedAnomaly.severity)}>
                            {selectedAnomaly.severity}
                          </Badge>
                          <h2 className="text-base font-bold text-ink">
                            {selectedAnomaly.metric_field} ({selectedAnomaly.period})
                          </h2>
                        </div>
                        <p className="text-xs text-slate mt-1">
                          Detected via <span className="font-medium text-ink">{selectedAnomaly.detection_method}</span> · Score: {selectedAnomaly.anomaly_score.toFixed(2)}
                        </p>
                      </div>

                      <div className="flex items-center gap-2">
                        {selectedAnomaly.status !== "ACKNOWLEDGED" && (
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => handleStatusUpdate(selectedAnomaly.id, "ACKNOWLEDGED")}
                          >
                            Acknowledge
                          </Button>
                        )}
                        {selectedAnomaly.status !== "RESOLVED" && (
                          <Button
                            variant="primary"
                            size="sm"
                            onClick={() => handleStatusUpdate(selectedAnomaly.id, "RESOLVED")}
                          >
                            Mark Resolved
                          </Button>
                        )}
                        {selectedAnomaly.status !== "DISMISSED" && (
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => handleStatusUpdate(selectedAnomaly.id, "DISMISSED")}
                          >
                            Dismiss
                          </Button>
                        )}
                      </div>
                    </div>

                    {/* Metric Cards Comparison */}
                    <div className="grid grid-cols-3 gap-3">
                      <div className="bg-cloud p-3.5 rounded-xl border border-border">
                        <span className="text-[11px] text-slate block">Observed Value</span>
                        <span className="text-base font-bold text-ink mt-0.5 block">
                          {selectedAnomaly.observed_value.toLocaleString()}
                        </span>
                      </div>
                      <div className="bg-cloud p-3.5 rounded-xl border border-border">
                        <span className="text-[11px] text-slate block">Baseline Expected</span>
                        <span className="text-base font-bold text-slate mt-0.5 block">
                          {selectedAnomaly.expected_value.toLocaleString()}
                        </span>
                      </div>
                      <div className="bg-cloud p-3.5 rounded-xl border border-border">
                        <span className="text-[11px] text-slate block">Deviation Delta</span>
                        <span className={`text-base font-bold mt-0.5 block ${selectedAnomaly.deviation < 0 ? "text-danger" : "text-teal"}`}>
                          {selectedAnomaly.deviation > 0 ? `+${selectedAnomaly.deviation.toLocaleString()}` : selectedAnomaly.deviation.toLocaleString()} ({selectedAnomaly.deviation_pct}%)
                        </span>
                      </div>
                    </div>

                    {/* Root Cause Subgroup Breakdown */}
                    <div className="space-y-3">
                      <div className="flex items-center justify-between">
                        <h4 className="text-xs font-semibold text-slate uppercase tracking-wider">
                          Dimensional Breakdown (Top Contributors)
                        </h4>
                        <span className="text-[11px] text-slate italic">Non-causal variance contribution</span>
                      </div>

                      {selectedAnomaly.root_causes.length === 0 ? (
                        <div className="text-xs text-slate bg-cloud p-4 rounded-xl text-center border border-border">
                          No categorical dimension was specified for root-cause decomposition.
                        </div>
                      ) : (
                        <div className="space-y-2.5">
                          {selectedAnomaly.root_causes.map((rc, idx) => (
                            <div key={idx} className="bg-cloud p-3.5 rounded-xl border border-border space-y-1.5">
                              <div className="flex items-center justify-between text-xs">
                                <span className="font-semibold text-ink">
                                  {rc.dimension_field}: <span className="text-teal">{rc.dimension_value}</span>
                                </span>
                                <span className="font-mono text-slate font-medium">{rc.contribution_pct}% contribution</span>
                              </div>
                              <div className="w-full h-2 bg-cloud-subtle rounded-full overflow-hidden border border-border-subtle">
                                <div
                                  className="h-full bg-teal rounded-full transition-all"
                                  style={{ width: `${Math.min(100, rc.contribution_pct)}%` }}
                                />
                              </div>
                              <p className="text-[11px] text-slate italic">{rc.narrative}</p>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  </Card>
                ) : (
                  <div className="text-center py-20 bg-surface rounded-2xl border border-border shadow-soft">
                    <p className="text-sm text-slate">Select an anomaly point to view details</p>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* VIEW: Table Evidence Fallback */}
          {viewMode === "table" && (
            <div className="bg-surface rounded-2xl border border-border shadow-soft overflow-hidden">
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs text-ink">
                  <thead className="bg-cloud text-slate border-b border-border font-semibold">
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
                  <tbody className="divide-y divide-border">
                    {filteredAnomalies.map((a) => (
                      <tr key={a.id} className="hover:bg-cloud-subtle transition-colors">
                        <td className="px-4 py-3">
                          <Badge variant={getSeverityBadgeVariant(a.severity)}>
                            {a.severity}
                          </Badge>
                        </td>
                        <td className="px-4 py-3 font-mono text-ink font-semibold">{a.period}</td>
                        <td className="px-4 py-3 font-medium text-ink">{a.metric_field}</td>
                        <td className="px-4 py-3 font-mono text-ink">{a.observed_value.toLocaleString()}</td>
                        <td className="px-4 py-3 font-mono text-slate">{a.expected_value.toLocaleString()}</td>
                        <td className="px-4 py-3 font-mono">
                          <span className={a.deviation < 0 ? "text-danger font-semibold" : "text-teal font-semibold"}>
                            {a.deviation > 0 ? `+${a.deviation.toLocaleString()}` : a.deviation.toLocaleString()} ({a.deviation_pct}%)
                          </span>
                        </td>
                        <td className="px-4 py-3 font-mono text-ink">{a.anomaly_score.toFixed(2)}</td>
                        <td className="px-4 py-3 text-slate">{a.detection_method}</td>
                        <td className="px-4 py-3">
                          <Badge variant={a.status === "RESOLVED" ? "teal" : a.status === "ACKNOWLEDGED" ? "blue" : "outline"}>
                            {a.status}
                          </Badge>
                        </td>
                        <td className="px-4 py-3 text-right">
                          <button
                            onClick={() => {
                              setSelectedAnomaly(a);
                              setViewMode("chart");
                            }}
                            className="text-teal hover:underline font-semibold"
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
