"use client";

import React, { useState, useEffect } from "react";
import {
  ForecastResponse,
  ForecastRunRequest,
  ForecastModelType,
  Dataset,
} from "@/types";
import {
  TrendingUp,
  Activity,
  AlertCircle,
  CheckCircle2,
  Calendar,
  Layers,
  Sparkles,
  BarChart3,
  Table as TableIcon,
  RefreshCw,
  Info,
  ShieldCheck,
  Zap,
} from "lucide-react";

interface ForecastWorkspaceProps {
  dataset?: Dataset;
  datasets?: Dataset[];
  token?: string;
  onForecastGenerated?: (forecast: ForecastResponse) => void;
}

export const ForecastWorkspace: React.FC<ForecastWorkspaceProps> = ({
  dataset: initialDataset,
  datasets = [],
  token,
  onForecastGenerated,
}) => {
  const [selectedDatasetId, setSelectedDatasetId] = useState<string>(
    initialDataset?.id || (datasets.length > 0 ? datasets[0].id : "")
  );
  const [targetField, setTargetField] = useState<string>("");
  const [timeField, setTimeField] = useState<string>("");
  const [frequency, setFrequency] = useState<string>("MS");
  const [horizon, setHorizon] = useState<number>(6);
  const [confidenceLevel, setConfidenceLevel] = useState<number>(0.95);
  const [modelType, setModelType] = useState<ForecastModelType>("AUTO");
  const [allowNegative, setAllowNegative] = useState<boolean>(false);

  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [progressStep, setProgressStep] = useState<string>("");
  const [forecastResult, setForecastResult] = useState<ForecastResponse | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [viewMode, setViewMode] = useState<"chart" | "table">("chart");
  const [showAdvanced, setShowAdvanced] = useState<boolean>(false);

  // Available numeric & datetime columns for selected dataset
  const currentDataset =
    initialDataset || datasets.find((d) => d.id === selectedDatasetId);

  useEffect(() => {
    if (initialDataset?.id) {
      setSelectedDatasetId(initialDataset.id);
    }
  }, [initialDataset]);

  const handleRunForecast = async () => {
    if (!selectedDatasetId || !targetField || !timeField) {
      setErrorMessage("Please specify target field and date column.");
      return;
    }

    setIsLoading(true);
    setErrorMessage(null);
    setProgressStep("Preparing time-series & regularizing frequency timeline…");

    try {
      setTimeout(() => setProgressStep("Training candidate models & cross-validating…"), 400);
      setTimeout(() => setProgressStep("Chronological backtesting with zero leakage…"), 800);
      setTimeout(() => setProgressStep("Generating prediction intervals & diagnostics…"), 1200);

      const payload: ForecastRunRequest = {
        dataset_id: selectedDatasetId,
        target_field: targetField,
        time_field: timeField,
        frequency: frequency || null,
        forecast_horizon: horizon,
        confidence_level: confidenceLevel,
        model_type: modelType,
        allow_negative: allowNegative,
      };

      const res = await fetch("/api/v1/forecasts/run", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        body: JSON.stringify(payload),
      });

      if (!res.ok) {
        const errorData = await res.json().catch(() => ({}));
        throw new Error(
          errorData.message || errorData.detail || `Forecasting failed (${res.status})`
        );
      }

      const result: ForecastResponse = await res.json();
      setForecastResult(result);
      if (onForecastGenerated) {
        onForecastGenerated(result);
      }
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Forecasting execution failed";
      setErrorMessage(msg);
    } finally {
      setIsLoading(false);
      setProgressStep("");
    }
  };

  // Combine historical and forecasted points for SVG line rendering
  const renderForecastChart = () => {
    if (!forecastResult) return null;

    const hist = forecastResult.historical_points || [];
    const pred = forecastResult.predictions || [];

    if (hist.length === 0 && pred.length === 0) {
      return (
        <div className="p-8 text-center text-slate-500">
          No temporal observations available to render chart.
        </div>
      );
    }

    const allValues = [
      ...hist.map((h) => h.actual),
      ...pred.map((p) => p.forecast),
      ...pred.map((p) => p.upper),
      ...pred.map((p) => p.lower),
    ];

    const minVal = Math.min(0, ...allValues);
    const maxVal = Math.max(1, ...allValues) * 1.08;
    const valRange = maxVal - minVal || 1;

    const width = 760;
    const height = 320;
    const padding = { top: 20, right: 30, bottom: 40, left: 60 };
    const chartW = width - padding.left - padding.right;
    const chartH = height - padding.top - padding.bottom;

    const totalSteps = hist.length + pred.length;
    const getX = (idx: number) => padding.left + (idx / Math.max(1, totalSteps - 1)) * chartW;
    const getY = (val: number) => padding.top + chartH - ((val - minVal) / valRange) * chartH;

    // Build historical path
    const histPath = hist
      .map((pt, i) => `${i === 0 ? "M" : "L"} ${getX(i)} ${getY(pt.actual)}`)
      .join(" ");

    // Build forecast path (starting from last historical point)
    const lastHistIdx = hist.length - 1;
    const lastHistVal = hist.length > 0 ? hist[lastHistIdx].actual : (pred[0]?.forecast ?? 0);

    const predPointsWithStart: Array<{ x: number; y: number; upper: number; lower: number }> = [
      { x: getX(lastHistIdx), y: getY(lastHistVal), upper: getY(lastHistVal), lower: getY(lastHistVal) },
      ...pred.map((pt, i) => ({
        x: getX(hist.length + i),
        y: getY(pt.forecast),
        upper: getY(pt.upper),
        lower: getY(pt.lower),
      })),
    ];

    const forecastPath = predPointsWithStart
      .map((pt, i) => `${i === 0 ? "M" : "L"} ${pt.x} ${pt.y}`)
      .join(" ");

    // Build prediction interval ribbon polygon (upper line forward, lower line backward)
    const upperRibbon = predPointsWithStart.map((p) => `${p.x},${p.upper}`);
    const lowerRibbon = [...predPointsWithStart].reverse().map((p) => `${p.x},${p.lower}`);
    const ribbonPolygon = `${upperRibbon.join(" ")} ${lowerRibbon.join(" ")}`;

    return (
      <div className="w-full bg-slate-900/60 border border-slate-800 rounded-xl p-4 backdrop-blur-md">
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center space-x-2">
            <span className="inline-block w-3 h-3 rounded-full bg-blue-500"></span>
            <span className="text-xs text-slate-300 font-medium">Historical Series</span>
            <span className="inline-block w-3 h-3 rounded-full bg-emerald-400 ml-3"></span>
            <span className="text-xs text-emerald-300 font-medium">Point Forecast</span>
            <span className="inline-block w-3 h-3 rounded-sm bg-emerald-500/20 border border-emerald-400/40 ml-3"></span>
            <span className="text-xs text-slate-400">
              {Math.round(forecastResult.confidence_level * 100)}% Prediction Interval
            </span>
          </div>
          <span className="text-xs text-slate-400 font-mono">
            Model: {forecastResult.selected_model_name}
          </span>
        </div>

        <svg
          viewBox={`0 0 ${width} ${height}`}
          className="w-full h-auto overflow-visible select-none"
          aria-label="Predictive Forecast Chart"
        >
          {/* Grid lines */}
          {[0, 0.25, 0.5, 0.75, 1.0].map((ratio) => {
            const y = padding.top + chartH * (1 - ratio);
            const val = minVal + ratio * valRange;
            return (
              <g key={ratio}>
                <line
                  x1={padding.left}
                  y1={y}
                  x2={width - padding.right}
                  y2={y}
                  stroke="rgba(148, 163, 184, 0.12)"
                  strokeDasharray="3 3"
                />
                <text
                  x={padding.left - 8}
                  y={y + 4}
                  textAnchor="end"
                  fontSize="10"
                  fill="#94a3b8"
                  fontFamily="monospace"
                >
                  {val >= 1000 ? `${(val / 1000).toFixed(1)}k` : val.toFixed(0)}
                </text>
              </g>
            );
          })}

          {/* Uncertainty Band Polygon */}
          <polygon
            points={ribbonPolygon}
            fill="rgba(16, 185, 129, 0.15)"
            stroke="rgba(16, 185, 129, 0.3)"
            strokeDasharray="2 2"
          />

          {/* Historical Series Line */}
          <path
            d={histPath}
            fill="none"
            stroke="#3b82f6"
            strokeWidth="2.5"
            strokeLinecap="round"
            strokeLinejoin="round"
          />

          {/* Historical Data Points */}
          {hist.map((pt, i) => (
            <circle
              key={`h-${i}`}
              cx={getX(i)}
              cy={getY(pt.actual)}
              r="3.5"
              fill="#1e293b"
              stroke="#3b82f6"
              strokeWidth="2"
            />
          ))}

          {/* Forecast Series Line */}
          <path
            d={forecastPath}
            fill="none"
            stroke="#10b981"
            strokeWidth="2.5"
            strokeDasharray="4 3"
            strokeLinecap="round"
            strokeLinejoin="round"
          />

          {/* Forecast Data Points */}
          {pred.map((pt, i) => {
            const cx = getX(hist.length + i);
            const cy = getY(pt.forecast);
            return (
              <g key={`p-${i}`}>
                <circle
                  cx={cx}
                  cy={cy}
                  r="4"
                  fill="#10b981"
                  stroke="#0f172a"
                  strokeWidth="2"
                />
              </g>
            );
          })}

          {/* X Axis Labels */}
          {hist.filter((_, idx) => idx % Math.max(1, Math.floor(hist.length / 4)) === 0).map((h, i) => {
            const origIdx = hist.indexOf(h);
            return (
              <text
                key={`xh-${i}`}
                x={getX(origIdx)}
                y={height - 12}
                textAnchor="middle"
                fontSize="10"
                fill="#94a3b8"
              >
                {h.date.substring(0, 7)}
              </text>
            );
          })}

          {pred.map((p, i) => (
            <text
              key={`xp-${i}`}
              x={getX(hist.length + i)}
              y={height - 12}
              textAnchor="middle"
              fontSize="10"
              fill="#34d399"
              fontWeight="600"
            >
              {p.date.substring(0, 7)}
            </text>
          ))}
        </svg>
      </div>
    );
  };

  return (
    <div className="w-full space-y-6">
      {/* Header & Title */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800 pb-4">
        <div>
          <div className="flex items-center space-x-2">
            <TrendingUp className="w-6 h-6 text-emerald-400" />
            <h2 className="text-xl font-bold text-white tracking-tight">
              Predictive Analytics & Forecasting Intelligence
            </h2>
          </div>
          <p className="text-sm text-slate-400 mt-1">
            Deterministic time-series forecasting with chronological cross-validation and prediction intervals.
          </p>
        </div>

        <div className="flex items-center space-x-3">
          <button
            onClick={() => setViewMode(viewMode === "chart" ? "table" : "chart")}
            className="flex items-center space-x-1.5 px-3 py-1.5 text-xs font-medium bg-slate-800 hover:bg-slate-700 text-slate-200 rounded-lg border border-slate-700 transition"
          >
            {viewMode === "chart" ? (
              <>
                <TableIcon className="w-3.5 h-3.5 text-slate-400" />
                <span>Table Fallback</span>
              </>
            ) : (
              <>
                <BarChart3 className="w-3.5 h-3.5 text-slate-400" />
                <span>Chart View</span>
              </>
            )}
          </button>

          <button
            onClick={handleRunForecast}
            disabled={isLoading || !targetField || !timeField}
            className="flex items-center space-x-2 px-4 py-2 text-sm font-semibold bg-emerald-600 hover:bg-emerald-500 disabled:bg-slate-800 disabled:text-slate-600 text-white rounded-lg shadow-lg shadow-emerald-900/20 transition"
          >
            {isLoading ? (
              <>
                <RefreshCw className="w-4 h-4 animate-spin text-white" />
                <span>Executing…</span>
              </>
            ) : (
              <>
                <Zap className="w-4 h-4 text-emerald-200" />
                <span>Run Forecast</span>
              </>
            )}
          </button>
        </div>
      </div>

      {/* Control Panel Grid */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 bg-slate-900/40 p-4 rounded-xl border border-slate-800">
        {/* Dataset Selection */}
        <div>
          <label className="block text-xs font-medium text-slate-400 mb-1">Dataset</label>
          <select
            value={selectedDatasetId}
            onChange={(e) => setSelectedDatasetId(e.target.value)}
            className="w-full bg-slate-800 text-slate-200 text-sm rounded-lg border border-slate-700 px-3 py-2 focus:ring-2 focus:ring-emerald-500 outline-none"
          >
            {datasets.map((d) => (
              <option key={d.id} value={d.id}>
                {d.name}
              </option>
            ))}
          </select>
        </div>

        {/* Target Field */}
        <div>
          <label className="block text-xs font-medium text-slate-400 mb-1">
            Target Variable (Numeric)
          </label>
          <input
            type="text"
            placeholder="e.g. revenue, sales, orders"
            value={targetField}
            onChange={(e) => setTargetField(e.target.value)}
            className="w-full bg-slate-800 text-slate-200 text-sm rounded-lg border border-slate-700 px-3 py-2 focus:ring-2 focus:ring-emerald-500 outline-none"
          />
        </div>

        {/* Time Field */}
        <div>
          <label className="block text-xs font-medium text-slate-400 mb-1">
            Time / Date Column
          </label>
          <input
            type="text"
            placeholder="e.g. order_date, date, timestamp"
            value={timeField}
            onChange={(e) => setTimeField(e.target.value)}
            className="w-full bg-slate-800 text-slate-200 text-sm rounded-lg border border-slate-700 px-3 py-2 focus:ring-2 focus:ring-emerald-500 outline-none"
          />
        </div>

        {/* Horizon */}
        <div>
          <label className="block text-xs font-medium text-slate-400 mb-1">
            Forecast Horizon ({horizon} periods)
          </label>
          <input
            type="range"
            min="1"
            max="36"
            value={horizon}
            onChange={(e) => setHorizon(parseInt(e.target.value, 10))}
            className="w-full accent-emerald-500 mt-2"
          />
        </div>
      </div>

      {/* Advanced Settings Toggle */}
      <div>
        <button
          onClick={() => setShowAdvanced(!showAdvanced)}
          className="text-xs text-slate-400 hover:text-slate-300 font-medium flex items-center space-x-1"
        >
          <span>{showAdvanced ? "Hide Advanced Options" : "Show Advanced Options (Model, Confidence, Frequency)"}</span>
        </button>

        {showAdvanced && (
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mt-3 bg-slate-900/30 p-4 rounded-xl border border-slate-800/80">
            <div>
              <label className="block text-xs font-medium text-slate-400 mb-1">Algorithm Strategy</label>
              <select
                value={modelType}
                onChange={(e) => setModelType(e.target.value as ForecastModelType)}
                className="w-full bg-slate-800 text-slate-200 text-sm rounded-lg border border-slate-700 px-3 py-2 outline-none"
              >
                <option value="AUTO">AUTO (Cross-Validated Best)</option>
                <option value="NAIVE">Naive Baseline</option>
                <option value="SEASONAL_NAIVE">Seasonal Naive</option>
                <option value="MOVING_AVERAGE">Moving Average</option>
                <option value="EXPONENTIAL_SMOOTHING">Exponential Smoothing (Holt-Winters)</option>
                <option value="ARIMA">ARIMA</option>
                <option value="SARIMA">SARIMA</option>
              </select>
            </div>

            <div>
              <label className="block text-xs font-medium text-slate-400 mb-1">Confidence Level</label>
              <select
                value={confidenceLevel}
                onChange={(e) => setConfidenceLevel(parseFloat(e.target.value))}
                className="w-full bg-slate-800 text-slate-200 text-sm rounded-lg border border-slate-700 px-3 py-2 outline-none"
              >
                <option value={0.8}>80% Prediction Interval</option>
                <option value={0.9}>90% Prediction Interval</option>
                <option value={0.95}>95% Prediction Interval (Default)</option>
              </select>
            </div>

            <div>
              <label className="block text-xs font-medium text-slate-400 mb-1">Timeline Frequency</label>
              <select
                value={frequency}
                onChange={(e) => setFrequency(e.target.value)}
                className="w-full bg-slate-800 text-slate-200 text-sm rounded-lg border border-slate-700 px-3 py-2 outline-none"
              >
                <option value="D">Daily (D)</option>
                <option value="W">Weekly (W)</option>
                <option value="MS">Monthly (MS)</option>
                <option value="QS">Quarterly (QS)</option>
                <option value="YS">Yearly (YS)</option>
              </select>
            </div>

            <div className="flex items-center space-x-2 mt-6">
              <input
                type="checkbox"
                id="allowNegative"
                checked={allowNegative}
                onChange={(e) => setAllowNegative(e.target.checked)}
                className="accent-emerald-500 rounded"
              />
              <label htmlFor="allowNegative" className="text-xs text-slate-300">
                Allow Negative Forecast Values
              </label>
            </div>
          </div>
        )}
      </div>

      {/* Loading Progress State */}
      {isLoading && (
        <div className="p-4 bg-emerald-950/20 border border-emerald-800/40 rounded-xl flex items-center space-x-3">
          <RefreshCw className="w-5 h-5 text-emerald-400 animate-spin flex-shrink-0" />
          <div>
            <div className="text-sm font-semibold text-emerald-300">Forecasting in progress</div>
            <div className="text-xs text-emerald-400/80">{progressStep}</div>
          </div>
        </div>
      )}

      {/* Error State */}
      {errorMessage && (
        <div className="p-4 bg-rose-950/20 border border-rose-800/40 rounded-xl flex items-center space-x-3">
          <AlertCircle className="w-5 h-5 text-rose-400 flex-shrink-0" />
          <div className="text-sm text-rose-200">{errorMessage}</div>
        </div>
      )}

      {/* Forecast Output Visualization */}
      {forecastResult && !isLoading && (
        <div className="space-y-6">
          {viewMode === "chart" ? (
            renderForecastChart()
          ) : (
            <div className="w-full bg-slate-900/60 border border-slate-800 rounded-xl p-4 overflow-x-auto">
              <h3 className="text-sm font-semibold text-white mb-3 flex items-center space-x-2">
                <TableIcon className="w-4 h-4 text-emerald-400" />
                <span>Forecast Data Points & Prediction Bounds</span>
              </h3>
              <table className="w-full text-left text-xs text-slate-300">
                <thead>
                  <tr className="border-b border-slate-800 text-slate-400">
                    <th className="py-2 px-3 font-semibold">Period Date</th>
                    <th className="py-2 px-3 font-semibold">Point Forecast</th>
                    <th className="py-2 px-3 font-semibold">Lower Bound ({Math.round(forecastResult.confidence_level * 100)}%)</th>
                    <th className="py-2 px-3 font-semibold">Upper Bound ({Math.round(forecastResult.confidence_level * 100)}%)</th>
                  </tr>
                </thead>
                <tbody>
                  {forecastResult.predictions.map((p, idx) => (
                    <tr key={idx} className="border-b border-slate-800/50 hover:bg-slate-800/30">
                      <td className="py-2 px-3 font-mono text-emerald-400">{p.date}</td>
                      <td className="py-2 px-3 font-semibold text-white">{p.forecast.toFixed(2)}</td>
                      <td className="py-2 px-3 text-slate-400">{p.lower.toFixed(2)}</td>
                      <td className="py-2 px-3 text-slate-400">{p.upper.toFixed(2)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {/* Diagnostics and Model Evaluation Card */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="bg-slate-900/40 border border-slate-800 rounded-xl p-4">
              <div className="text-xs text-slate-400 font-medium">Selected Model</div>
              <div className="text-base font-bold text-white mt-1">
                {forecastResult.selected_model_name}
              </div>
              <div className="text-xs text-emerald-400 mt-2 flex items-center space-x-1">
                <CheckCircle2 className="w-3.5 h-3.5" />
                <span>{forecastResult.metrics.relative_improvement_pct >= 0 ? `+${forecastResult.metrics.relative_improvement_pct}% vs baseline` : "Baseline Selected"}</span>
              </div>
            </div>

            <div className="bg-slate-900/40 border border-slate-800 rounded-xl p-4">
              <div className="text-xs text-slate-400 font-medium">Holdout Backtest MAE</div>
              <div className="text-base font-bold text-white mt-1">
                {forecastResult.metrics.mae.toFixed(2)}
              </div>
              <div className="text-xs text-slate-400 mt-2">
                RMSE: {forecastResult.metrics.rmse.toFixed(2)}
              </div>
            </div>

            <div className="bg-slate-900/40 border border-slate-800 rounded-xl p-4">
              <div className="text-xs text-slate-400 font-medium">Mean Error (MAPE / sMAPE)</div>
              <div className="text-base font-bold text-white mt-1">
                {forecastResult.metrics.mape.toFixed(1)}% / {forecastResult.metrics.smape.toFixed(1)}%
              </div>
              <div className="text-xs text-slate-400 mt-2">
                Baseline MAE: {forecastResult.metrics.baseline_mae.toFixed(2)}
              </div>
            </div>

            <div className="bg-slate-900/40 border border-slate-800 rounded-xl p-4">
              <div className="text-xs text-slate-400 font-medium">Diagnostics</div>
              <div className="text-sm font-semibold text-white mt-1">
                {forecastResult.diagnostics.observations_count} Observations
              </div>
              <div className="text-xs text-slate-400 mt-2">
                {forecastResult.diagnostics.seasonality_detected
                  ? `Seasonality: Period ${forecastResult.diagnostics.seasonality_period || 12}`
                  : "No Seasonality Detected"}
              </div>
            </div>
          </div>

          {/* Provenance Footer */}
          <div className="p-3 bg-slate-950/50 border border-slate-800/80 rounded-lg flex flex-wrap items-center justify-between text-xs text-slate-400 gap-2">
            <div className="flex items-center space-x-2">
              <ShieldCheck className="w-4 h-4 text-emerald-400" />
              <span>
                Forecast Provenance: Dataset Version <code className="text-slate-300">{forecastResult.dataset_version_id.substring(0, 8)}</code>
              </span>
            </div>
            <div>
              Execution Time: <span className="text-slate-300">{forecastResult.execution_time_ms} ms</span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
