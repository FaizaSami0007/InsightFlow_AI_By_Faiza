"use client";

import React, { useState, useEffect } from "react";
import {
  Dataset,
  ScenarioResultResponse,
  ScenarioType,
  AssumptionSpec,
  AssumptionOperation,
  WhatIfScenarioRequest,
  SensitivityAnalysisRequest,
  ScenarioComparisonRequest,
  ScenarioBranchSpec,
  SensitivityStep,
  ScenarioComparisonItem,
} from "@/types";
import {
  SlidersHorizontal,
  TrendingUp,
  TrendingDown,
  Percent,
  Plus,
  Trash2,
  Play,
  RotateCcw,
  CheckCircle2,
  AlertTriangle,
  Info,
  ShieldCheck,
  FileSpreadsheet,
  Download,
  Layers,
  BarChart3,
  GitBranch,
  ArrowRight,
  Sparkles,
} from "lucide-react";

interface ScenarioWorkspaceProps {
  dataset?: Dataset;
  datasets?: Dataset[];
  token?: string;
  onScenarioCompleted?: (result: ScenarioResultResponse) => void;
}

export const ScenarioWorkspace: React.FC<ScenarioWorkspaceProps> = ({
  dataset: initialDataset,
  datasets = [],
  token,
  onScenarioCompleted,
}) => {
  const [selectedDatasetId, setSelectedDatasetId] = useState<string>(
    initialDataset?.id || (datasets.length > 0 ? datasets[0].id : "")
  );
  const [activeTab, setActiveTab] = useState<"what_if" | "sensitivity" | "comparison">("what_if");
  const [targetMetric, setTargetMetric] = useState<string>("revenue");
  const [scenarioName, setScenarioName] = useState<string>("");

  // What-If State
  const [assumptions, setAssumptions] = useState<AssumptionSpec[]>([
    {
      variable: "price",
      operation: "PERCENTAGE_CHANGE",
      value: 5.0,
      unit: "%",
    },
  ]);

  // Sensitivity State
  const [sweepVariable, setSweepVariable] = useState<string>("price");
  const [rangeMinPct, setRangeMinPct] = useState<number>(-20.0);
  const [rangeMaxPct, setRangeMaxPct] = useState<number>(20.0);
  const [stepPct, setStepPct] = useState<number>(5.0);

  // Comparison State
  const [comparisonBranches, setComparisonBranches] = useState<Array<{ name: string; variable: string; deltaPct: number }>>([
    { name: "Optimistic Case", variable: "price", deltaPct: 10.0 },
    { name: "Conservative Case", variable: "price", deltaPct: -10.0 },
    { name: "Aggressive Case", variable: "price", deltaPct: 25.0 },
  ]);

  // Execution & Status State
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [progressStep, setProgressStep] = useState<string>("");
  const [result, setResult] = useState<ScenarioResultResponse | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [showPreviewModal, setShowPreviewModal] = useState<boolean>(false);

  const currentDataset = initialDataset || datasets.find((d) => d.id === selectedDatasetId);

  useEffect(() => {
    if (initialDataset?.id) {
      setSelectedDatasetId(initialDataset.id);
    }
  }, [initialDataset]);

  const handleAddAssumption = () => {
    setAssumptions([
      ...assumptions,
      {
        variable: "units",
        operation: "PERCENTAGE_CHANGE",
        value: 0.0,
        unit: "%",
      },
    ]);
  };

  const handleRemoveAssumption = (index: number) => {
    if (assumptions.length > 1) {
      setAssumptions(assumptions.filter((_, i) => i !== index));
    }
  };

  const handleUpdateAssumption = (index: number, updates: Partial<AssumptionSpec>) => {
    setAssumptions(
      assumptions.map((a, i) => (i === index ? { ...a, ...updates } : a))
    );
  };

  const handleRunSimulation = async () => {
    if (!selectedDatasetId || !targetMetric) {
      setErrorMessage("Please select a target metric and dataset.");
      return;
    }

    setIsLoading(true);
    setErrorMessage(null);
    setProgressStep("Loading immutable baseline snapshot from DuckDB…");

    try {
      setTimeout(() => setProgressStep("Applying deterministic assumption transformations…"), 300);
      setTimeout(() => setProgressStep("Verifying physical domain bounds & calculating delta…"), 600);

      let url = "/api/v1/scenarios/what-if";
      let body: unknown = {};

      if (activeTab === "what_if") {
        url = "/api/v1/scenarios/what-if";
        const payload: WhatIfScenarioRequest = {
          dataset_id: selectedDatasetId,
          name: scenarioName || `${targetMetric} What-If Simulation`,
          target_metric: targetMetric,
          assumptions: assumptions,
        };
        body = payload;
      } else if (activeTab === "sensitivity") {
        url = "/api/v1/scenarios/sensitivity";
        const payload: SensitivityAnalysisRequest = {
          dataset_id: selectedDatasetId,
          name: scenarioName || `${sweepVariable} Sensitivity on ${targetMetric}`,
          target_metric: targetMetric,
          sweep_variable: sweepVariable,
          min_pct: rangeMinPct,
          max_pct: rangeMaxPct,
          step_pct: stepPct,
        };
        body = payload;
      } else if (activeTab === "comparison") {
        url = "/api/v1/scenarios/compare";
        const scenarioMap: Record<string, AssumptionSpec[]> = {};
        comparisonBranches.forEach((b) => {
          scenarioMap[b.name] = [
            {
              variable: b.variable,
              operation: "PERCENTAGE_CHANGE",
              value: b.deltaPct,
              unit: "%",
            },
          ];
        });
        body = {
          dataset_id: selectedDatasetId,
          name: scenarioName || `${targetMetric} Scenario Comparison`,
          target_metric: targetMetric,
          scenarios: scenarioMap,
        };
      }

      const headers: Record<string, string> = {
        "Content-Type": "application/json",
      };
      if (token) {
        headers["Authorization"] = `Bearer ${token}`;
      }

      const res = await fetch(url, {
        method: "POST",
        headers,
        body: JSON.stringify(body),
      });

      if (!res.ok) {
        const errorData = await res.json().catch(() => ({ detail: "Scenario execution failed" }));
        throw new Error(errorData.detail || `Server error: ${res.status}`);
      }

      const data: ScenarioResultResponse = await res.json();
      setResult(data);
      if (onScenarioCompleted) {
        onScenarioCompleted(data);
      }
    } catch (err: unknown) {
      setErrorMessage(err instanceof Error ? err.message : "Failed to execute scenario simulation.");
    } finally {
      setIsLoading(false);
      setProgressStep("");
    }
  };

  const exportCSV = () => {
    if (!result) return;
    let csvContent = "data:text/csv;charset=utf-8,";

    if (result.scenario_type === "SENSITIVITY" && result.steps) {
      csvContent += "Step,Variable,DeltaPct,SimulatedDriver,SimulatedTarget,AbsoluteChange,PercentageChange\n";
      result.steps.forEach((s) => {
        csvContent += `${s.step_index},${s.variable},${s.delta_pct || 0},${s.simulated_driver_value},${s.outcome_value},${s.absolute_change},${s.percentage_change || ""}\n`;
      });
    } else if (result.scenario_type === "COMPARISON" && result.comparisons) {
      csvContent += "Branch,SimulatedValue,AbsoluteChange,PercentageChange,Narrative\n";
      result.comparisons.forEach((c) => {
        csvContent += `"${c.branch_name}",${c.outcome_value},${c.absolute_change},${c.percentage_change || ""},"${c.narrative || ""}"\n`;
      });
    } else {
      csvContent += "Metric,Type,Value,ChangePct\n";
      csvContent += `${result.target_metric},Baseline,${result.baseline_value},0%\n`;
      csvContent += `${result.target_metric},Scenario,${result.scenario_value},${result.percentage_change || 0}%\n`;
    }

    const encodedUri = encodeURI(csvContent);
    const link = document.createElement("a");
    link.setAttribute("href", encodedUri);
    link.setAttribute("download", `scenario_${result.name.toLowerCase().replace(/\s+/g, "_")}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  return (
    <div className="space-y-6">
      {/* Header Banner */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 bg-surface p-6 rounded-2xl border border-border shadow-soft">
        <div>
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-teal-soft text-teal border border-teal-border">
              <SlidersHorizontal className="w-5 h-5" />
            </div>
            <div>
              <h1 className="text-xl font-bold text-ink flex items-center gap-2">
                Decision Intelligence & Scenario Simulation
              </h1>
              <p className="text-xs text-slate mt-0.5">
                Deterministic what-if modeling, sensitivity parameter sweeps, and branch comparisons with guaranteed source data immutability.
              </p>
            </div>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-teal-soft border border-teal-border text-teal text-xs font-medium">
            <ShieldCheck className="w-4 h-4" />
            <span>Immutable Source Data</span>
          </div>
          <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-blue-soft border border-blue-border text-blue text-xs font-medium">
            <Sparkles className="w-4 h-4" />
            <span>Zero Hallucination</span>
          </div>
        </div>
      </div>

      {/* Main Workspace Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Column: Configuration & Assumptions */}
        <div className="lg:col-span-5 space-y-5">
          {/* Controls Card */}
          <div className="bg-surface rounded-2xl border border-border p-5 shadow-soft space-y-4">
            <div className="flex items-center justify-between border-b border-border pb-3">
              <span className="text-xs font-semibold uppercase tracking-wider text-slate">
                Simulation Setup
              </span>
              {/* Type Switcher */}
              <div className="flex bg-cloud p-1 rounded-lg border border-border">
                <button
                  type="button"
                  onClick={() => setActiveTab("what_if")}
                  className={`px-2.5 py-1 text-xs font-medium rounded-md transition-all ${
                    activeTab === "what_if"
                      ? "bg-teal text-white shadow-soft"
                      : "text-slate hover:text-ink"
                  }`}
                >
                  What-If
                </button>
                <button
                  type="button"
                  onClick={() => setActiveTab("sensitivity")}
                  className={`px-2.5 py-1 text-xs font-medium rounded-md transition-all ${
                    activeTab === "sensitivity"
                      ? "bg-teal text-white shadow-soft"
                      : "text-slate hover:text-ink"
                  }`}
                >
                  Sensitivity
                </button>
                <button
                  type="button"
                  onClick={() => setActiveTab("comparison")}
                  className={`px-2.5 py-1 text-xs font-medium rounded-md transition-all ${
                    activeTab === "comparison"
                      ? "bg-teal text-white shadow-soft"
                      : "text-slate hover:text-ink"
                  }`}
                >
                  Comparison
                </button>
              </div>
            </div>

            {/* Target Metric Selection */}
            <div>
              <label className="block text-xs font-medium text-ink mb-1.5">
                Target Outcome Metric
              </label>
              <input
                type="text"
                value={targetMetric}
                onChange={(e) => setTargetMetric(e.target.value)}
                placeholder="e.g. revenue, gross_profit, orders"
                className="w-full px-3 py-2 bg-cloud-subtle border border-border rounded-lg text-sm text-ink placeholder-slate focus:outline-none focus:ring-2 focus:ring-teal"
              />
            </div>

            {/* Scenario Name (Optional) */}
            <div>
              <label className="block text-xs font-medium text-ink mb-1.5">
                Scenario Name
              </label>
              <input
                type="text"
                value={scenarioName}
                onChange={(e) => setScenarioName(e.target.value)}
                placeholder="e.g. 2026 Optimistic Growth Model"
                className="w-full px-3 py-2 bg-cloud-subtle border border-border rounded-lg text-sm text-ink placeholder-slate focus:outline-none focus:ring-2 focus:ring-teal"
              />
            </div>

            {/* TAB 1: WHAT-IF ASSUMPTIONS BUILDER */}
            {activeTab === "what_if" && (
              <div className="space-y-3 pt-2">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-semibold text-ink">
                    Structured Assumptions ({assumptions.length})
                  </span>
                  <button
                    type="button"
                    onClick={handleAddAssumption}
                    className="flex items-center gap-1 text-xs text-teal hover:text-teal-hover font-medium transition-colors"
                  >
                    <Plus className="w-3.5 h-3.5" />
                    Add Driver
                  </button>
                </div>

                <div className="space-y-3 max-h-[320px] overflow-y-auto pr-1">
                  {assumptions.map((assumption, idx) => (
                    <div
                      key={idx}
                      className="p-3 bg-cloud-subtle rounded-xl border border-border space-y-2.5 relative group"
                    >
                      <div className="flex items-center justify-between">
                        <span className="text-xs font-medium text-teal">
                          Driver #{idx + 1}
                        </span>
                        {assumptions.length > 1 && (
                          <button
                            type="button"
                            onClick={() => handleRemoveAssumption(idx)}
                            className="text-slate hover:text-danger transition-colors p-1"
                          >
                            <Trash2 className="w-3.5 h-3.5" />
                          </button>
                        )}
                      </div>

                      <div className="grid grid-cols-2 gap-2">
                        <div>
                          <label className="block text-[10px] text-slate uppercase tracking-wider mb-1">
                            Variable
                          </label>
                          <input
                            type="text"
                            value={assumption.variable}
                            onChange={(e) =>
                              handleUpdateAssumption(idx, { variable: e.target.value })
                            }
                            className="w-full px-2.5 py-1.5 bg-surface border border-border rounded-lg text-xs text-ink focus:outline-none focus:ring-2 focus:ring-teal"
                            placeholder="e.g. price"
                          />
                        </div>
                        <div>
                          <label className="block text-[10px] text-slate uppercase tracking-wider mb-1">
                            Operation
                          </label>
                          <select
                            value={assumption.operation}
                            onChange={(e) =>
                              handleUpdateAssumption(idx, {
                                operation: e.target.value as AssumptionOperation,
                              })
                            }
                            className="w-full px-2.5 py-1.5 bg-surface border border-border rounded-lg text-xs text-ink focus:outline-none focus:ring-2 focus:ring-teal"
                          >
                            <option value="PERCENTAGE_CHANGE">Percentage Change (%)</option>
                            <option value="ABSOLUTE_CHANGE">Absolute Delta (+/-)</option>
                            <option value="DIRECT_SET">Direct Set (=)</option>
                          </select>
                        </div>
                      </div>

                      <div>
                        <div className="flex items-center justify-between text-xs mb-1">
                          <span className="text-slate">Modifier Value</span>
                          <span className="font-mono text-teal font-medium">
                            {assumption.value > 0 ? `+${assumption.value}` : assumption.value}
                            {assumption.operation === "PERCENTAGE_CHANGE" ? "%" : ""}
                          </span>
                        </div>
                        <input
                          type="range"
                          min={assumption.operation === "PERCENTAGE_CHANGE" ? -50 : -1000}
                          max={assumption.operation === "PERCENTAGE_CHANGE" ? 50 : 1000}
                          step={assumption.operation === "PERCENTAGE_CHANGE" ? 0.5 : 10}
                          value={assumption.value}
                          onChange={(e) =>
                            handleUpdateAssumption(idx, { value: parseFloat(e.target.value) })
                          }
                          className="w-full h-1.5 bg-border rounded-lg appearance-none cursor-pointer accent-teal"
                        />
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* TAB 2: SENSITIVITY CONFIGURATION */}
            {activeTab === "sensitivity" && (
              <div className="space-y-3 pt-2">
                <div>
                  <label className="block text-xs font-medium text-ink mb-1">
                    Sweep Variable
                  </label>
                  <input
                    type="text"
                    value={sweepVariable}
                    onChange={(e) => setSweepVariable(e.target.value)}
                    placeholder="e.g. price, marketing_spend"
                    className="w-full px-3 py-2 bg-cloud-subtle border border-border rounded-lg text-xs text-ink focus:outline-none focus:ring-2 focus:ring-teal"
                  />
                </div>

                <div className="grid grid-cols-3 gap-2">
                  <div>
                    <label className="block text-[10px] text-slate uppercase tracking-wider mb-1">
                      Min %
                    </label>
                    <input
                      type="number"
                      value={rangeMinPct}
                      onChange={(e) => setRangeMinPct(parseFloat(e.target.value))}
                      className="w-full px-2.5 py-1.5 bg-cloud-subtle border border-border rounded-lg text-xs text-ink focus:outline-none focus:ring-2 focus:ring-teal"
                    />
                  </div>
                  <div>
                    <label className="block text-[10px] text-slate uppercase tracking-wider mb-1">
                      Max %
                    </label>
                    <input
                      type="number"
                      value={rangeMaxPct}
                      onChange={(e) => setRangeMaxPct(parseFloat(e.target.value))}
                      className="w-full px-2.5 py-1.5 bg-cloud-subtle border border-border rounded-lg text-xs text-ink focus:outline-none focus:ring-2 focus:ring-teal"
                    />
                  </div>
                  <div>
                    <label className="block text-[10px] text-slate uppercase tracking-wider mb-1">
                      Step %
                    </label>
                    <input
                      type="number"
                      value={stepPct}
                      onChange={(e) => setStepPct(parseFloat(e.target.value))}
                      className="w-full px-2.5 py-1.5 bg-cloud-subtle border border-border rounded-lg text-xs text-ink focus:outline-none focus:ring-2 focus:ring-teal"
                    />
                  </div>
                </div>
              </div>
            )}

            {/* TAB 3: COMPARISON BRANCHES */}
            {activeTab === "comparison" && (
              <div className="space-y-3 pt-2">
                <span className="text-xs font-semibold text-ink">
                  Scenario Branches ({comparisonBranches.length})
                </span>
                <div className="space-y-2 max-h-[280px] overflow-y-auto">
                  {comparisonBranches.map((branch, idx) => (
                    <div
                      key={idx}
                      className="p-2.5 bg-cloud-subtle rounded-xl border border-border flex items-center justify-between text-xs"
                    >
                      <div className="flex items-center gap-2">
                        <GitBranch className="w-3.5 h-3.5 text-teal" />
                        <input
                          type="text"
                          value={branch.name}
                          onChange={(e) =>
                            setComparisonBranches(
                              comparisonBranches.map((b, i) =>
                                i === idx ? { ...b, name: e.target.value } : b
                              )
                            )
                          }
                          className="bg-transparent text-ink font-medium focus:outline-none border-b border-transparent focus:border-teal"
                        />
                      </div>
                      <div className="flex items-center gap-1.5 font-mono">
                        <span className="text-slate">{branch.variable}:</span>
                        <span className={branch.deltaPct >= 0 ? "text-teal font-semibold" : "text-danger font-semibold"}>
                          {branch.deltaPct >= 0 ? `+${branch.deltaPct}%` : `${branch.deltaPct}%`}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Error Message */}
            {errorMessage && (
              <div className="p-3 bg-danger-soft border border-danger/20 rounded-xl flex items-start gap-2.5 text-xs text-danger">
                <AlertTriangle className="w-4 h-4 text-danger flex-shrink-0 mt-0.5" />
                <span>{errorMessage}</span>
              </div>
            )}

            {/* Execution Buttons */}
            <div className="pt-2">
              <button
                type="button"
                onClick={handleRunSimulation}
                disabled={isLoading}
                className="w-full py-2.5 px-4 bg-teal hover:bg-teal-hover disabled:opacity-50 text-white font-medium text-sm rounded-xl shadow-soft flex items-center justify-center gap-2 transition-all active:scale-[0.99]"
              >
                {isLoading ? (
                  <>
                    <RotateCcw className="w-4 h-4 animate-spin text-white" />
                    <span>Simulating…</span>
                  </>
                ) : (
                  <>
                    <Play className="w-4 h-4 fill-current" />
                    <span>Run Deterministic Scenario</span>
                  </>
                )}
              </button>
            </div>
          </div>
        </div>

        {/* Right Column: Simulation Results & Visualizations */}
        <div className="lg:col-span-7 space-y-5">
          {isLoading && (
            <div className="bg-surface rounded-2xl border border-border p-12 text-center space-y-4 shadow-soft">
              <div className="inline-flex p-4 rounded-full bg-teal-soft border border-teal-border text-teal animate-pulse">
                <RotateCcw className="w-8 h-8 animate-spin" />
              </div>
              <h3 className="text-base font-semibold text-ink">
                Simulating Scenario Context
              </h3>
              <p className="text-xs text-slate max-w-md mx-auto">{progressStep}</p>
            </div>
          )}

          {!isLoading && !result && (
            <div className="bg-surface rounded-2xl border border-dashed border-border p-12 text-center space-y-3 shadow-soft">
              <div className="p-3 bg-cloud-subtle rounded-full inline-flex text-slate">
                <SlidersHorizontal className="w-6 h-6" />
              </div>
              <h3 className="text-sm font-medium text-ink">
                No Scenario Executed Yet
              </h3>
              <p className="text-xs text-slate max-w-sm mx-auto">
                Configure your what-if drivers, sensitivity parameters, or branch cases on the left and click &quot;Run Deterministic Scenario&quot;.
              </p>
            </div>
          )}

          {!isLoading && result && (
            <div className="space-y-5">
              {/* Actual vs Simulation Metric Comparison Cards */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {/* Baseline Card */}
                <div className="bg-surface rounded-2xl border border-border p-5 space-y-1 shadow-soft relative overflow-hidden">
                  <div className="text-[10px] font-bold uppercase tracking-wider text-slate flex items-center gap-1.5">
                    <span className="w-2 h-2 rounded-full bg-slate"></span>
                    ACTUAL (BASELINE)
                  </div>
                  <div className="text-2xl font-bold font-mono text-ink">
                    {result.baseline_value.toLocaleString(undefined, {
                      minimumFractionDigits: 2,
                      maximumFractionDigits: 2,
                    })}
                  </div>
                  <div className="text-xs text-slate flex items-center gap-1">
                    <span>Source: {result.baseline_source}</span>
                  </div>
                </div>

                {/* Scenario Card */}
                <div className="bg-teal-soft/30 rounded-2xl border border-teal-border p-5 space-y-1 shadow-soft relative overflow-hidden">
                  <div className="text-[10px] font-bold uppercase tracking-wider text-teal flex items-center gap-1.5">
                    <span className="w-2 h-2 rounded-full bg-teal animate-pulse"></span>
                    SIMULATION (SCENARIO)
                  </div>
                  <div className="text-2xl font-bold font-mono text-teal flex items-center gap-3">
                    {result.scenario_value.toLocaleString(undefined, {
                      minimumFractionDigits: 2,
                      maximumFractionDigits: 2,
                    })}
                    {result.percentage_change !== null && result.percentage_change !== undefined && (
                      <span
                        className={`text-xs px-2 py-0.5 rounded-md font-sans font-semibold flex items-center gap-0.5 ${
                          result.percentage_change >= 0
                            ? "bg-teal-soft text-teal border border-teal-border"
                            : "bg-danger-soft text-danger border border-danger/20"
                        }`}
                      >
                        {result.percentage_change >= 0 ? (
                          <TrendingUp className="w-3.5 h-3.5" />
                        ) : (
                          <TrendingDown className="w-3.5 h-3.5" />
                        )}
                        {result.percentage_change >= 0
                          ? `+${result.percentage_change.toFixed(2)}%`
                          : `${result.percentage_change.toFixed(2)}%`}
                      </span>
                    )}
                  </div>
                  <div className="text-xs text-slate">
                    Delta:{" "}
                    <span className="font-mono text-ink font-medium">
                      {result.absolute_change >= 0
                        ? `+${result.absolute_change.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`
                        : result.absolute_change.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                    </span>
                  </div>
                </div>
              </div>

              {/* Narrative Summary */}
              {result.narrative && (
                <div className="p-4 bg-surface rounded-2xl border border-border text-xs text-ink shadow-soft flex items-start gap-3">
                  <Info className="w-4 h-4 text-teal flex-shrink-0 mt-0.5" />
                  <p className="leading-relaxed text-slate">{result.narrative}</p>
                </div>
              )}

              {/* SENSITIVITY SWEEP TABLE & CURVE */}
              {result.scenario_type === "SENSITIVITY" && result.steps && (
                <div className="bg-surface rounded-2xl border border-border p-5 space-y-4 shadow-soft">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-semibold uppercase tracking-wider text-ink flex items-center gap-1.5">
                      <BarChart3 className="w-4 h-4 text-teal" />
                      Sensitivity Response Curve
                    </span>
                    <button
                      type="button"
                      onClick={exportCSV}
                      className="flex items-center gap-1 text-xs text-slate hover:text-ink px-2.5 py-1 rounded-lg bg-cloud border border-border hover:bg-cloud-subtle transition-colors"
                    >
                      <Download className="w-3.5 h-3.5" />
                      Export CSV
                    </button>
                  </div>

                  <div className="overflow-x-auto">
                    <table className="w-full text-xs text-left text-ink">
                      <thead className="bg-cloud-subtle text-slate uppercase text-[10px] tracking-wider border-b border-border">
                        <tr>
                          <th className="py-2.5 px-3">Variation</th>
                          <th className="py-2.5 px-3">Driver Value</th>
                          <th className="py-2.5 px-3">Simulated {result.target_metric}</th>
                          <th className="py-2.5 px-3">Delta</th>
                          <th className="py-2.5 px-3">Change %</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-border font-mono">
                        {result.steps.map((step, idx) => (
                          <tr
                            key={idx}
                            className={`hover:bg-cloud-subtle/50 transition-colors ${
                              step.delta_pct === 0 ? "bg-teal-soft/40 font-bold" : ""
                            }`}
                          >
                            <td className="py-2 px-3 text-ink">
                              {step.delta_pct !== null && step.delta_pct !== undefined
                                ? step.delta_pct >= 0
                                ? `+${step.delta_pct}%`
                                : `${step.delta_pct}%`
                                : "—"}
                            </td>
                            <td className="py-2 px-3 text-slate">
                              {step.simulated_driver_value.toFixed(2)}
                            </td>
                            <td className="py-2 px-3 text-ink font-semibold">
                              {step.outcome_value.toLocaleString(undefined, {
                                minimumFractionDigits: 2,
                                maximumFractionDigits: 2,
                              })}
                            </td>
                            <td className="py-2 px-3 text-slate">
                              {step.absolute_change >= 0
                                ? `+${step.absolute_change.toFixed(2)}`
                                : step.absolute_change.toFixed(2)}
                            </td>
                            <td
                              className={`py-2 px-3 font-semibold ${
                                (step.percentage_change || 0) >= 0
                                  ? "text-teal"
                                  : "text-danger"
                              }`}
                            >
                              {step.percentage_change !== null && step.percentage_change !== undefined
                                ? step.percentage_change >= 0
                                  ? `+${step.percentage_change.toFixed(2)}%`
                                  : `${step.percentage_change.toFixed(2)}%`
                                : "N/A"}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}

              {/* COMPARISON BRANCHES TABLE */}
              {result.scenario_type === "COMPARISON" && result.comparisons && (
                <div className="bg-surface rounded-2xl border border-border p-5 space-y-4 shadow-soft">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-semibold uppercase tracking-wider text-ink flex items-center gap-1.5">
                      <GitBranch className="w-4 h-4 text-teal" />
                      Side-by-Side Branch Comparison
                    </span>
                    <button
                      type="button"
                      onClick={exportCSV}
                      className="flex items-center gap-1 text-xs text-slate hover:text-ink px-2.5 py-1 rounded-lg bg-cloud border border-border hover:bg-cloud-subtle transition-colors"
                    >
                      <Download className="w-3.5 h-3.5" />
                      Export CSV
                    </button>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                    {result.comparisons.map((c, idx) => (
                      <div
                        key={idx}
                        className="p-4 bg-cloud-subtle rounded-xl border border-border space-y-2 hover:border-teal-border transition-all"
                      >
                        <span className="text-xs font-semibold text-teal block">
                          {c.branch_name}
                        </span>
                        <div className="text-xl font-bold font-mono text-ink">
                          {c.outcome_value.toLocaleString(undefined, {
                            minimumFractionDigits: 2,
                            maximumFractionDigits: 2,
                          })}
                        </div>
                        <div className="text-xs flex items-center justify-between text-slate">
                          <span>Delta:</span>
                          <span
                            className={`font-mono font-semibold ${
                              (c.percentage_change || 0) >= 0 ? "text-teal" : "text-danger"
                            }`}
                          >
                            {c.percentage_change !== null && c.percentage_change !== undefined
                              ? c.percentage_change >= 0
                                ? `+${c.percentage_change.toFixed(2)}%`
                                : `${c.percentage_change.toFixed(2)}%`
                              : "N/A"}
                          </span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Provenance Box */}
              <div className="p-3.5 bg-cloud-subtle rounded-xl border border-border text-[11px] text-slate flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <ShieldCheck className="w-4 h-4 text-teal" />
                  <span>
                    Deterministic Engine:{" "}
                    <code className="text-ink font-mono">{result.engine_version}</code>
                  </span>
                </div>
                <div className="font-mono text-[10px] text-slate">
                  Scenario ID: {result.id}
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
