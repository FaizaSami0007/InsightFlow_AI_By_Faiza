"use client";

import * as React from "react";
import {
  Activity,
  Award,
  CheckCircle2,
  Cpu,
  Database,
  GitBranch,
  Layers,
  RotateCcw,
  Search,
  ShieldAlert,
  ShieldCheck,
  ArrowRight,
} from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import {
  MLModelAlertResponse,
  MLModelResponse,
  MLModelVersionResponse,
  MLModelVersionStatus,
} from "@/types";

export function ModelOperationsView() {
  const [activeTab, setActiveTab] = React.useState<"registry" | "monitoring" | "lineage" | "alerts">("registry");
  const [searchQuery, setSearchQuery] = React.useState("");
  const [selectedType, setSelectedType] = React.useState<string>("ALL");
  const [selectedModel, setSelectedModel] = React.useState<MLModelResponse | null>(null);
  const [selectedVersion, setSelectedVersion] = React.useState<MLModelVersionResponse | null>(null);
  const [isPromoting, setIsPromoting] = React.useState(false);
  const [promotionTarget, setPromotionTarget] = React.useState<MLModelVersionStatus>("VALIDATED");
  const [promotionReason, setPromotionReason] = React.useState("");

  // Initial state for demonstration
  const [models] = React.useState<MLModelResponse[]>([
    {
      id: "mod-101",
      user_id: "usr-01",
      name: "SARIMA Enterprise Revenue Forecaster",
      description: "Deterministic seasonal time-series predictor for regional revenue streams.",
      model_type: "FORECASTING",
      task_type: "TIME_SERIES_FORECAST",
      framework: "statsmodels",
      provider: "insightflow_native",
      status: "ACTIVE",
      owner: "finance-analytics",
      tags: ["revenue", "q4-planning", "production"],
      metadata_json: { target_column: "revenue", frequency: "monthly" },
      versions_count: 2,
      active_production_version: "v1.2.0",
      health_status: "GOOD",
      created_at: new Date(Date.now() - 86400000 * 14).toISOString(),
      updated_at: new Date().toISOString(),
    },
    {
      id: "mod-102",
      user_id: "usr-01",
      name: "Multivariate Isolation Forest Anomaly Detector",
      description: "High-frequency streaming telemetry spike & novelty detection.",
      model_type: "ANOMALY_DETECTION",
      task_type: "OUTLIER_DETECTION",
      framework: "scikit-learn",
      provider: "insightflow_native",
      status: "ACTIVE",
      owner: "ops-monitoring",
      tags: ["telemetry", "infrastructure", "high-priority"],
      metadata_json: { contamination: 0.01 },
      versions_count: 3,
      active_production_version: "v2.0.1",
      health_status: "WARNING",
      created_at: new Date(Date.now() - 86400000 * 30).toISOString(),
      updated_at: new Date().toISOString(),
    },
    {
      id: "mod-103",
      user_id: "usr-01",
      name: "Customer Retention Churn Classifier",
      description: "Gradient boosted tree predicting 30-day enterprise renewal probability.",
      model_type: "CLASSIFICATION",
      task_type: "BINARY_CLASSIFICATION",
      framework: "scikit-learn",
      provider: "insightflow_native",
      status: "ACTIVE",
      owner: "growth-team",
      tags: ["churn", "crm", "customer-success"],
      metadata_json: { threshold: 0.65 },
      versions_count: 1,
      active_production_version: "v1.0.0",
      health_status: "GOOD",
      created_at: new Date(Date.now() - 86400000 * 5).toISOString(),
      updated_at: new Date().toISOString(),
    },
  ]);

  const [versions, setVersions] = React.useState<MLModelVersionResponse[]>([
    {
      id: "ver-101",
      model_id: "mod-101",
      model_name: "SARIMA Enterprise Revenue Forecaster",
      model_type: "FORECASTING",
      version: "v1.2.0",
      artifact_location: "artifacts/models/sarima_rev_v1.2.0.pkl",
      checksum: "a3f4e198b20c94da83921b7f6e5d4c3b2a109876543210fedcba9876543210ab",
      training_dataset_id: "ds-q4-sales",
      training_dataset_version_id: "dv-3",
      feature_schema: {
        features: {
          revenue: { data_type: "numeric", is_required: true, min_value: 0 },
          orders: { data_type: "numeric", is_required: true, min_value: 0 },
          region: { data_type: "categorical", allowed_categories: ["North", "South", "East", "West"] },
        },
      },
      preprocessing_version: "v1.1.0",
      parameters: { order: [1, 1, 1], seasonal_order: [1, 1, 0, 12] },
      metrics: { mae: 1420.5, rmse: 2150.0, mape: 3.8, smape: 3.7, mase: 0.64 },
      baseline_metrics: { mae: 2350.0, rmse: 3400.0, mape: 7.2 },
      status: "PRODUCTION",
      approval_record: { approved_by: "lead_data_scientist", approved_at: new Date().toISOString() },
      health_status: "GOOD",
      health_details: { overall_score: 94.5 },
      created_at: new Date(Date.now() - 86400000 * 7).toISOString(),
      updated_at: new Date().toISOString(),
    },
    {
      id: "ver-102",
      model_id: "mod-101",
      model_name: "SARIMA Enterprise Revenue Forecaster",
      model_type: "FORECASTING",
      version: "v1.3.0-rc1",
      artifact_location: "artifacts/models/sarima_rev_v1.3.0.pkl",
      checksum: "e8b2c4d9a1f7630251849a6c7d8e9f0123456789abcdef0123456789abcdef01",
      training_dataset_id: "ds-q4-sales",
      training_dataset_version_id: "dv-4",
      feature_schema: {
        features: {
          revenue: { data_type: "numeric", is_required: true },
          orders: { data_type: "numeric", is_required: true },
          region: { data_type: "categorical" },
          promo_flag: { data_type: "numeric" },
        },
      },
      preprocessing_version: "v1.2.0",
      parameters: { order: [2, 1, 2], seasonal_order: [1, 1, 1, 12] },
      metrics: { mae: 1180.2, rmse: 1820.0, mape: 3.1, smape: 3.0, mase: 0.52 },
      baseline_metrics: { mae: 2350.0, rmse: 3400.0, mape: 7.2 },
      status: "STAGED",
      approval_record: null,
      health_status: "GOOD",
      health_details: { overall_score: 96.0 },
      created_at: new Date(Date.now() - 86400000 * 1).toISOString(),
      updated_at: new Date().toISOString(),
    },
  ]);

  const [alerts, setAlerts] = React.useState<MLModelAlertResponse[]>([
    {
      id: "alt-01",
      model_id: "mod-102",
      model_name: "Multivariate Isolation Forest Anomaly Detector",
      alert_type: "FEATURE_DRIFT",
      severity: "WARNING",
      metric_name: "cpu_usage_psi",
      observed_value: 0.168,
      threshold: 0.1,
      message: "Moderate feature drift detected on telemetry column 'cpu_usage' (PSI: 0.168).",
      evidence: { max_psi: 0.168, drifted_feature: "cpu_usage" },
      is_acknowledged: false,
      created_at: new Date(Date.now() - 3600000 * 4).toISOString(),
    },
  ]);

  const activeModel = selectedModel || models[0];
  const activeVersion = selectedVersion || versions[0];

  const filteredModels = models.filter((m) => {
    const matchesSearch =
      m.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      m.description?.toLowerCase().includes(searchQuery.toLowerCase()) ||
      m.tags.some((t) => t.toLowerCase().includes(searchQuery.toLowerCase()));
    const matchesType = selectedType === "ALL" || m.model_type === selectedType;
    return matchesSearch && matchesType;
  });

  const handleAcknowledgeAlert = (alertId: string) => {
    setAlerts((prev) =>
      prev.map((a) => (a.id === alertId ? { ...a, is_acknowledged: true } : a))
    );
  };

  const handlePromoteVersion = (targetStatus: MLModelVersionStatus) => {
    if (!activeVersion) return;
    setVersions((prev) =>
      prev.map((v) =>
        v.id === activeVersion.id
          ? {
              ...v,
              status: targetStatus,
              approval_record: {
                approved_by: "Workspace Lead (UI Action)",
                reason: promotionReason || "Manual promotion via Model Operations Dashboard",
                approved_at: new Date().toISOString(),
              },
            }
          : targetStatus === "PRODUCTION" && v.model_id === activeVersion.model_id
          ? { ...v, status: "DEPRECATED" as MLModelVersionStatus }
          : v
      )
    );
    setIsPromoting(false);
    setPromotionReason("");
  };

  const getStatusBadgeVariant = (status: MLModelVersionStatus | string) => {
    switch (status) {
      case "PRODUCTION":
      case "GOOD":
      case "HEALTHY":
        return "teal";
      case "STAGED":
      case "VALIDATED":
        return "blue";
      case "WARNING":
      case "VALIDATING":
        return "amber";
      case "CRITICAL":
      case "FAILED":
        return "danger";
      default:
        return "outline";
    }
  };

  return (
    <div className="space-y-6">
      {/* 1. Header & Overview KPIs */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2">
              <Cpu className="h-6 w-6 text-teal-400" />
              Production MLOps & Model Operations
            </h1>
            <Badge variant="teal" dot>
              Phase 16 Complete
            </Badge>
          </div>
          <p className="text-sm text-slate-400">
            Model registry, version lifecycle state machine, PSI/KS drift detection, and multi-factor health monitoring.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <Button
            variant={activeTab === "registry" ? "primary" : "outline"}
            size="sm"
            onClick={() => setActiveTab("registry")}
            className="text-xs"
          >
            <Layers className="h-3.5 w-3.5 mr-1.5" />
            Registry & Versions
          </Button>
          <Button
            variant={activeTab === "monitoring" ? "primary" : "outline"}
            size="sm"
            onClick={() => setActiveTab("monitoring")}
            className="text-xs"
          >
            <Activity className="h-3.5 w-3.5 mr-1.5" />
            Drift & Health
          </Button>
          <Button
            variant={activeTab === "lineage" ? "primary" : "outline"}
            size="sm"
            onClick={() => setActiveTab("lineage")}
            className="text-xs"
          >
            <GitBranch className="h-3.5 w-3.5 mr-1.5" />
            Lineage DAG
          </Button>
          <Button
            variant={activeTab === "alerts" ? "primary" : "outline"}
            size="sm"
            onClick={() => setActiveTab("alerts")}
            className="text-xs relative"
          >
            <ShieldAlert className="h-3.5 w-3.5 mr-1.5" />
            Alerts
            {alerts.filter((a) => !a.is_acknowledged).length > 0 && (
              <span className="ml-1.5 flex h-4 w-4 items-center justify-center rounded-full bg-amber-500 text-[10px] font-bold text-slate-950">
                {alerts.filter((a) => !a.is_acknowledged).length}
              </span>
            )}
          </Button>
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <Card className="bg-slate-900/60 border-slate-800 backdrop-blur-sm">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-xs font-medium text-slate-400">Registered Models</CardTitle>
            <Layers className="h-4 w-4 text-teal-400" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-white">{models.length}</div>
            <p className="text-xs text-slate-500 mt-1">Across 8 task families</p>
          </CardContent>
        </Card>

        <Card className="bg-slate-900/60 border-slate-800 backdrop-blur-sm">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-xs font-medium text-slate-400">Production Deployments</CardTitle>
            <Award className="h-4 w-4 text-blue-400" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-white">
              {models.filter((m) => m.active_production_version).length}
            </div>
            <p className="text-xs text-slate-500 mt-1">100% baseline superiority</p>
          </CardContent>
        </Card>

        <Card className="bg-slate-900/60 border-slate-800 backdrop-blur-sm">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-xs font-medium text-slate-400">Statistical Drift Status</CardTitle>
            <Activity className="h-4 w-4 text-emerald-400" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-emerald-400">NOMINAL</div>
            <p className="text-xs text-slate-500 mt-1">Max PSI 0.04 (threshold 0.2)</p>
          </CardContent>
        </Card>

        <Card className="bg-slate-900/60 border-slate-800 backdrop-blur-sm">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-xs font-medium text-slate-400">Monitoring Alerts</CardTitle>
            <ShieldAlert className="h-4 w-4 text-amber-400" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-amber-400">
              {alerts.filter((a) => !a.is_acknowledged).length} Active
            </div>
            <p className="text-xs text-slate-500 mt-1">1 unacknowledged warning</p>
          </CardContent>
        </Card>
      </div>

      {/* 2. Main Tab Contents */}
      {activeTab === "registry" && (
        <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
          {/* Left: Model List & Filter */}
          <div className="space-y-4 lg:col-span-1">
            <div className="flex items-center gap-2">
              <div className="relative flex-1">
                <Search className="absolute left-3 top-2.5 h-3.5 w-3.5 text-slate-400" />
                <input
                  type="text"
                  placeholder="Search models, tags..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="w-full rounded-lg border border-slate-800 bg-slate-900/80 px-8 py-2 text-xs text-white placeholder-slate-500 focus:border-teal-500 focus:outline-none"
                />
              </div>
            </div>

            <div className="flex flex-wrap gap-1.5">
              {["ALL", "FORECASTING", "ANOMALY_DETECTION", "CLASSIFICATION"].map((t) => (
                <button
                  key={t}
                  onClick={() => setSelectedType(t)}
                  className={`rounded-md px-2.5 py-1 text-[11px] font-medium transition-colors ${
                    selectedType === t
                      ? "bg-teal-500/20 text-teal-300 border border-teal-500/40"
                      : "bg-slate-900 text-slate-400 hover:text-slate-200 border border-slate-800"
                  }`}
                >
                  {t}
                </button>
              ))}
            </div>

            <div className="space-y-2">
              {filteredModels.map((m) => {
                const isSelected = activeModel?.id === m.id;
                return (
                  <div
                    key={m.id}
                    onClick={() => setSelectedModel(m)}
                    className={`cursor-pointer rounded-xl border p-3.5 transition-all ${
                      isSelected
                        ? "border-teal-500/50 bg-slate-900/90 shadow-lg shadow-teal-950/20"
                        : "border-slate-800/80 bg-slate-900/40 hover:border-slate-700 hover:bg-slate-900/60"
                    }`}
                  >
                    <div className="flex items-start justify-between gap-2">
                      <div className="space-y-1">
                        <div className="text-xs font-semibold text-white">{m.name}</div>
                        <div className="text-[11px] text-slate-400 line-clamp-2">{m.description}</div>
                      </div>
                      <Badge variant={getStatusBadgeVariant(m.health_status)}>
                        {m.health_status}
                      </Badge>
                    </div>

                    <div className="mt-3 flex items-center justify-between text-[11px] text-slate-500">
                      <span className="font-mono text-slate-400">{m.framework}</span>
                      <span>{m.versions_count} versions</span>
                      {m.active_production_version && (
                        <span className="text-teal-400 font-medium">Prod: {m.active_production_version}</span>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Right: Model Version Details & Actions */}
          <div className="space-y-6 lg:col-span-2">
            {activeModel && (
              <Card className="border-slate-800 bg-slate-900/60 backdrop-blur-sm">
                <CardHeader className="pb-3 border-b border-slate-800">
                  <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
                    <div>
                      <div className="flex items-center gap-2">
                        <CardTitle className="text-base text-white">{activeModel.name}</CardTitle>
                        <Badge variant="blue">{activeModel.model_type}</Badge>
                      </div>
                      <CardDescription className="text-xs mt-1">
                        Task: {activeModel.task_type} • Provider: {activeModel.provider} • Owner: {activeModel.owner}
                      </CardDescription>
                    </div>

                    <div className="flex items-center gap-2">
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => setIsPromoting(true)}
                        className="text-xs border-teal-500/40 text-teal-300 hover:bg-teal-500/10"
                      >
                        <Award className="h-3.5 w-3.5 mr-1.5" />
                        Promote / Transition
                      </Button>
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => handlePromoteVersion("PRODUCTION")}
                        className="text-xs border-amber-500/40 text-amber-300 hover:bg-amber-500/10"
                      >
                        <RotateCcw className="h-3.5 w-3.5 mr-1.5" />
                        Rollback
                      </Button>
                    </div>
                  </div>
                </CardHeader>

                <CardContent className="pt-4 space-y-6">
                  {/* Versions Table */}
                  <div>
                    <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-400 mb-3">
                      Registered Versions & Lineage Checksums
                    </h3>
                    <div className="overflow-x-auto rounded-lg border border-slate-800">
                      <table className="w-full text-left text-xs text-slate-300">
                        <thead className="bg-slate-950/60 text-[11px] uppercase text-slate-400">
                          <tr>
                            <th className="px-3 py-2">Version</th>
                            <th className="px-3 py-2">Status</th>
                            <th className="px-3 py-2">Validation Metrics</th>
                            <th className="px-3 py-2">Baseline Impr.</th>
                            <th className="px-3 py-2">Checksum</th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-800">
                          {versions.map((v) => (
                            <tr
                              key={v.id}
                              onClick={() => setSelectedVersion(v)}
                              className={`cursor-pointer transition-colors ${
                                activeVersion?.id === v.id ? "bg-teal-950/20" : "hover:bg-slate-900/50"
                              }`}
                            >
                              <td className="px-3 py-2.5 font-medium text-white">{v.version}</td>
                              <td className="px-3 py-2.5">
                                <Badge variant={getStatusBadgeVariant(v.status)}>{v.status}</Badge>
                              </td>
                              <td className="px-3 py-2.5 font-mono text-slate-300">
                                MAE: {v.metrics?.mae ?? "N/A"} • MAPE: {v.metrics?.mape ?? "N/A"}%
                              </td>
                              <td className="px-3 py-2.5 text-emerald-400 font-medium">+39.5%</td>
                              <td className="px-3 py-2.5 font-mono text-[10px] text-slate-500">
                                {v.checksum.slice(0, 16)}...
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>

                  {/* Feature Contract Schema */}
                  <div>
                    <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-400 mb-3">
                      Input Feature Contract & Schema Spec
                    </h3>
                    <div className="rounded-lg border border-slate-800 bg-slate-950/50 p-3 font-mono text-xs text-slate-300">
                      <pre className="overflow-x-auto">
                        {JSON.stringify(activeVersion?.feature_schema, null, 2)}
                      </pre>
                    </div>
                  </div>
                </CardContent>
              </Card>
            )}
          </div>
        </div>
      )}

      {/* 3. Monitoring & 5-Dimension Health Tab */}
      {activeTab === "monitoring" && (
        <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
          <div className="lg:col-span-2 space-y-6">
            <Card className="border-slate-800 bg-slate-900/60 backdrop-blur-sm">
              <CardHeader className="pb-3 border-b border-slate-800">
                <div className="flex items-center justify-between">
                  <CardTitle className="text-base text-white flex items-center gap-2">
                    <Activity className="h-4 w-4 text-teal-400" />
                    5-Factor Explainable Model Health Indicator
                  </CardTitle>
                  <Badge variant="teal">94.5 / 100 Overall</Badge>
                </div>
                <CardDescription className="text-xs">
                  Decomposed score avoiding black-box opacity across data quality, drift, accuracy, latency, and freshness.
                </CardDescription>
              </CardHeader>
              <CardContent className="pt-4 space-y-4">
                <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
                  <div className="rounded-lg border border-slate-800 bg-slate-950/40 p-3">
                    <div className="flex items-center justify-between text-xs">
                      <span className="text-slate-400">1. Data Quality</span>
                      <span className="text-emerald-400 font-semibold">100 / 100</span>
                    </div>
                    <p className="text-[11px] text-slate-500 mt-1">0% missingness, complete schema alignment</p>
                  </div>

                  <div className="rounded-lg border border-slate-800 bg-slate-950/40 p-3">
                    <div className="flex items-center justify-between text-xs">
                      <span className="text-slate-400">2. Statistical Drift (PSI)</span>
                      <span className="text-emerald-400 font-semibold">95 / 100</span>
                    </div>
                    <p className="text-[11px] text-slate-500 mt-1">Max PSI 0.042 (well below 0.1 threshold)</p>
                  </div>

                  <div className="rounded-lg border border-slate-800 bg-slate-950/40 p-3">
                    <div className="flex items-center justify-between text-xs">
                      <span className="text-slate-400">3. Baseline Superiority</span>
                      <span className="text-emerald-400 font-semibold">96 / 100</span>
                    </div>
                    <p className="text-[11px] text-slate-500 mt-1">39.5% MAE reduction over Seasonal Naive</p>
                  </div>

                  <div className="rounded-lg border border-slate-800 bg-slate-950/40 p-3">
                    <div className="flex items-center justify-between text-xs">
                      <span className="text-slate-400">4. Latency SLA</span>
                      <span className="text-emerald-400 font-semibold">100 / 100</span>
                    </div>
                    <p className="text-[11px] text-slate-500 mt-1">Avg 24.5ms (budget 250ms)</p>
                  </div>
                </div>

                <div className="rounded-lg border border-teal-500/20 bg-teal-950/10 p-3.5">
                  <div className="text-xs font-semibold text-teal-300 flex items-center gap-1.5">
                    <CheckCircle2 className="h-4 w-4 text-teal-400" />
                    Automated Health Assessment
                  </div>
                  <p className="text-xs text-slate-300 mt-1">
                    All monitoring dimensions are healthy and operating within nominal parameters. No retraining required.
                  </p>
                </div>
              </CardContent>
            </Card>
          </div>

          <div className="space-y-6">
            <Card className="border-slate-800 bg-slate-900/60 backdrop-blur-sm">
              <CardHeader className="pb-3 border-b border-slate-800">
                <CardTitle className="text-sm text-white">Statistical Drift Analysis</CardTitle>
                <CardDescription className="text-xs">Continuous evaluation vs reference baseline</CardDescription>
              </CardHeader>
              <CardContent className="pt-4 space-y-3 text-xs">
                <div className="flex justify-between items-center py-1.5 border-b border-slate-800/60">
                  <span className="text-slate-400">Metric Engine</span>
                  <span className="font-mono text-slate-200">Laplace-smoothed PSI + 2-Sample KS</span>
                </div>
                <div className="flex justify-between items-center py-1.5 border-b border-slate-800/60">
                  <span className="text-slate-400">Categorical Distance</span>
                  <span className="font-mono text-slate-200">Total Variation Distance (TVD)</span>
                </div>
                <div className="flex justify-between items-center py-1.5 border-b border-slate-800/60">
                  <span className="text-slate-400">Prediction Drift</span>
                  <span className="text-emerald-400 font-medium">None Detected</span>
                </div>
                <div className="flex justify-between items-center py-1.5">
                  <span className="text-slate-400">Last Evaluated</span>
                  <span className="text-slate-400">12 minutes ago</span>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      )}

      {/* 4. Lineage DAG Tab */}
      {activeTab === "lineage" && (
        <Card className="border-slate-800 bg-slate-900/60 backdrop-blur-sm">
          <CardHeader className="pb-3 border-b border-slate-800">
            <CardTitle className="text-base text-white flex items-center gap-2">
              <GitBranch className="h-4 w-4 text-teal-400" />
              End-to-End Model Provenance & Prediction Lineage DAG
            </CardTitle>
            <CardDescription className="text-xs">
              Direct acyclic graph tracing training dataset version &rarr; preprocessing pipeline &rarr; model artifact &rarr; production deployment.
            </CardDescription>
          </CardHeader>
          <CardContent className="pt-6">
            <div className="flex flex-col md:flex-row items-center justify-between gap-4 p-4 rounded-xl bg-slate-950/60 border border-slate-800">
              {/* Node 1: Dataset */}
              <div className="flex flex-col items-center p-3 rounded-lg border border-slate-800 bg-slate-900/80 w-full md:w-56 text-center">
                <Database className="h-6 w-6 text-blue-400 mb-2" />
                <span className="text-xs font-semibold text-white">Dataset: ds-q4-sales</span>
                <span className="text-[10px] text-slate-400 mt-0.5">Version dv-3 (3,600 rows)</span>
              </div>

              <ArrowRight className="h-5 w-5 text-slate-600 hidden md:block" />

              {/* Node 2: Pipeline */}
              <div className="flex flex-col items-center p-3 rounded-lg border border-slate-800 bg-slate-900/80 w-full md:w-56 text-center">
                <Layers className="h-6 w-6 text-teal-400 mb-2" />
                <span className="text-xs font-semibold text-white">Feature Contract v1.1.0</span>
                <span className="text-[10px] text-slate-400 mt-0.5">3 features validated</span>
              </div>

              <ArrowRight className="h-5 w-5 text-slate-600 hidden md:block" />

              {/* Node 3: Model */}
              <div className="flex flex-col items-center p-3 rounded-lg border border-teal-500/40 bg-teal-950/20 w-full md:w-56 text-center">
                <Cpu className="h-6 w-6 text-teal-300 mb-2" />
                <span className="text-xs font-semibold text-white">SARIMA v1.2.0</span>
                <span className="text-[10px] text-teal-400 mt-0.5">SHA-256 Validated</span>
              </div>

              <ArrowRight className="h-5 w-5 text-slate-600 hidden md:block" />

              {/* Node 4: Deployment */}
              <div className="flex flex-col items-center p-3 rounded-lg border border-slate-800 bg-slate-900/80 w-full md:w-56 text-center">
                <ShieldCheck className="h-6 w-6 text-emerald-400 mb-2" />
                <span className="text-xs font-semibold text-white">Production Cluster</span>
                <span className="text-[10px] text-emerald-400 mt-0.5">Active Deployment</span>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* 5. Alerts Tab */}
      {activeTab === "alerts" && (
        <Card className="border-slate-800 bg-slate-900/60 backdrop-blur-sm">
          <CardHeader className="pb-3 border-b border-slate-800">
            <CardTitle className="text-base text-white flex items-center gap-2">
              <ShieldAlert className="h-4 w-4 text-amber-400" />
              MLOps Monitoring Alerts & Action Center
            </CardTitle>
            <CardDescription className="text-xs">
              Automated alerts triggered by statistical drift, threshold violations, or model degradation.
            </CardDescription>
          </CardHeader>
          <CardContent className="pt-4 space-y-3">
            {alerts.length === 0 ? (
              <div className="text-center py-8 text-xs text-slate-500">No active alerts recorded.</div>
            ) : (
              alerts.map((a) => (
                <div
                  key={a.id}
                  className={`flex items-start justify-between p-3.5 rounded-lg border ${
                    a.is_acknowledged
                      ? "border-slate-800/60 bg-slate-950/30 opacity-60"
                      : "border-amber-500/30 bg-amber-950/10"
                  }`}
                >
                  <div className="space-y-1">
                    <div className="flex items-center gap-2">
                      <Badge variant={a.severity === "CRITICAL" ? "danger" : "amber"}>{a.severity}</Badge>
                      <span className="text-xs font-semibold text-white">{a.model_name}</span>
                      <span className="text-[11px] text-slate-400 font-mono">({a.metric_name})</span>
                    </div>
                    <p className="text-xs text-slate-300">{a.message}</p>
                    <div className="text-[10px] text-slate-500 font-mono">
                      Observed: {a.observed_value} • Threshold: {a.threshold} • Time:{" "}
                      {new Date(a.created_at).toLocaleTimeString()}
                    </div>
                  </div>

                  {!a.is_acknowledged && (
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => handleAcknowledgeAlert(a.id)}
                      className="text-xs border-amber-500/40 text-amber-300 hover:bg-amber-500/10"
                    >
                      Acknowledge
                    </Button>
                  )}
                </div>
              ))
            )}
          </CardContent>
        </Card>
      )}

      {/* Promotion Modal Dialog */}
      {isPromoting && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/80 backdrop-blur-sm p-4">
          <div className="w-full max-w-md rounded-xl border border-slate-800 bg-slate-900 p-5 shadow-2xl space-y-4">
            <h3 className="text-base font-semibold text-white flex items-center gap-2">
              <Award className="h-4 w-4 text-teal-400" />
              Promote Model Version {activeVersion?.version}
            </h3>
            <p className="text-xs text-slate-400">
              State transitions require human approval notes and adhere to strict MLOps policy gates.
            </p>

            <div className="space-y-3">
              <div>
                <label className="text-xs font-medium text-slate-300 block mb-1">Target Lifecycle Stage</label>
                <select
                  value={promotionTarget}
                  onChange={(e) => setPromotionTarget(e.target.value as MLModelVersionStatus)}
                  className="w-full rounded-lg border border-slate-800 bg-slate-950 px-3 py-2 text-xs text-white"
                >
                  <option value="VALIDATING">VALIDATING</option>
                  <option value="VALIDATED">VALIDATED</option>
                  <option value="STAGED">STAGED</option>
                  <option value="PRODUCTION">PRODUCTION</option>
                  <option value="DEPRECATED">DEPRECATED</option>
                  <option value="RETIRED">RETIRED</option>
                </select>
              </div>

              <div>
                <label className="text-xs font-medium text-slate-300 block mb-1">Approval & Change Notes</label>
                <textarea
                  value={promotionReason}
                  onChange={(e) => setPromotionReason(e.target.value)}
                  placeholder="e.g. Offline backtesting passed with +39.5% MAE superiority over baseline."
                  rows={3}
                  className="w-full rounded-lg border border-slate-800 bg-slate-950 p-2.5 text-xs text-white placeholder-slate-500 focus:border-teal-500 focus:outline-none"
                />
              </div>
            </div>

            <div className="flex justify-end gap-2 pt-2">
              <Button size="sm" variant="outline" onClick={() => setIsPromoting(false)} className="text-xs">
                Cancel
              </Button>
              <Button
                size="sm"
                onClick={() => handlePromoteVersion(promotionTarget)}
                className="text-xs bg-teal-600 hover:bg-teal-500 text-white"
              >
                Confirm Transition
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
