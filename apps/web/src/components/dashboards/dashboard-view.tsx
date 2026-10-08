"use client";

import * as React from "react";
import {
  Sparkles,
  RefreshCw,
  Edit3,
  Check,
  ShieldCheck,
  Calendar,
  Layers,
  Send,
  Download,
  Share2,
} from "lucide-react";
import {
  Dashboard,
  DashboardWidget,
  DashboardPatch,
  DashboardQualityReport,
  ChartType,
} from "@/types";
import { DashboardWidgetCard } from "./dashboard-widget";
import { DashboardFilterBar } from "./dashboard-filter-bar";
import { DashboardExportModal } from "./dashboard-export-modal";
import { DashboardShareModal } from "./dashboard-share-modal";
import { Dialog } from "@/components/ui/dialog";
import { cn } from "@/lib/utils";
import { api } from "@/lib/api-client";

interface DashboardViewProps {
  initialDashboard: Dashboard;
  onRefresh?: (dashboardId: string) => Promise<void>;
  onDelete?: (dashboardId: string) => Promise<void>;
  onSavePatches?: (dashboardId: string, patches: DashboardPatch[]) => Promise<Dashboard>;
  onRefineWithAI?: (dashboardId: string, prompt: string) => Promise<Dashboard>;
}

export function DashboardView({
  initialDashboard,
  onRefresh,
  onSavePatches,
  onRefineWithAI,
}: DashboardViewProps) {
  const [dashboard, setDashboard] = React.useState<Dashboard>(initialDashboard);
  const [isEditMode, setIsEditMode] = React.useState(false);
  const [isRefreshing, setIsRefreshing] = React.useState(false);
  const [isRefining, setIsRefining] = React.useState(false);
  const [refinePrompt, setRefinePrompt] = React.useState("");
  const [activeFilters, setActiveFilters] = React.useState<Record<string, unknown>>({});
  const [qualityModalOpen, setQualityModalOpen] = React.useState(false);
  const [exportModalOpen, setExportModalOpen] = React.useState(false);
  const [shareModalOpen, setShareModalOpen] = React.useState(false);
  const [qualityReport, setQualityReport] = React.useState<DashboardQualityReport | null>(null);
  const [isLoadingQuality, setIsLoadingQuality] = React.useState(false);
  const [inspectWidget, setInspectWidget] = React.useState<DashboardWidget | null>(null);
  const [feedbackMessage, setFeedbackMessage] = React.useState<{ text: string; type: "success" | "error" | "info" } | null>(null);

  // Sync state if initialDashboard changes externally
  React.useEffect(() => {
    setDashboard(initialDashboard);
  }, [initialDashboard]);

  // Clear feedback after 4 seconds
  React.useEffect(() => {
    if (feedbackMessage) {
      const timer = setTimeout(() => setFeedbackMessage(null), 4000);
      return () => clearTimeout(timer);
    }
  }, [feedbackMessage]);

  const handleRefresh = async () => {
    setIsRefreshing(true);
    try {
      if (onRefresh) {
        await onRefresh(dashboard.id);
      } else {
        const updated = await api.post<Dashboard>(`/api/v1/dashboards/${dashboard.id}/refresh`, {
          filter_values: activeFilters,
        });
        setDashboard(updated);
        setFeedbackMessage({ text: "Dashboard refreshed with latest analytical results.", type: "success" });
      }
    } catch {
      setFeedbackMessage({ text: "Failed to refresh dashboard.", type: "error" });
    } finally {
      setIsRefreshing(false);
    }
  };

  const handleApplyFilter = (columnName: string, value: unknown) => {
    setActiveFilters((prev) => ({ ...prev, [columnName]: value }));
  };

  const handleClearFilter = (columnName: string) => {
    setActiveFilters((prev) => {
      const copy = { ...prev };
      delete copy[columnName];
      return copy;
    });
  };

  const handleRemoveWidget = async (widgetId: string) => {
    const patch: DashboardPatch = {
      op: "REMOVE_WIDGET",
      widget_id: widgetId,
      params: {},
    };
    await applySinglePatch(patch, "Widget removed.");
  };

  const handleMoveWidget = async (widgetId: string, direction: "up" | "down" | "left" | "right") => {
    const widget = dashboard.widgets.find((w) => w.id === widgetId);
    if (!widget) return;

    let newX = widget.grid_x;
    let newY = widget.grid_y;

    if (direction === "left") newX = Math.max(0, newX - 1);
    if (direction === "right") newX = Math.min(12 - widget.grid_w, newX + 1);
    if (direction === "up") newY = Math.max(0, newY - 1);
    if (direction === "down") newY = newY + 1;

    const patch: DashboardPatch = {
      op: "MOVE_WIDGET",
      widget_id: widgetId,
      params: {
        grid_x: newX,
        grid_y: newY,
        grid_w: widget.grid_w,
        grid_h: widget.grid_h,
      },
    };
    await applySinglePatch(patch);
  };

  const handleResizeWidget = async (widgetId: string, gridW: number, gridH: number) => {
    const patch: DashboardPatch = {
      op: "RESIZE_WIDGET",
      widget_id: widgetId,
      params: {
        grid_w: gridW,
        grid_h: gridH,
      },
    };
    await applySinglePatch(patch, `Widget resized to ${gridW} columns.`);
  };

  const handleChangeChartType = async (widgetId: string, chartType: ChartType) => {
    const patch: DashboardPatch = {
      op: "CHANGE_CHART",
      widget_id: widgetId,
      params: {
        chart_type: chartType,
      },
    };
    await applySinglePatch(patch, `Chart changed to ${chartType}.`);
  };

  const applySinglePatch = async (patch: DashboardPatch, successMsg?: string) => {
    try {
      if (onSavePatches) {
        const updated = await onSavePatches(dashboard.id, [patch]);
        setDashboard(updated);
        if (successMsg) setFeedbackMessage({ text: successMsg, type: "success" });
      } else {
        const updated = await api.patch<Dashboard>(`/api/v1/dashboards/${dashboard.id}/patches`, {
          patches: [patch],
        });
        setDashboard(updated);
        if (successMsg) setFeedbackMessage({ text: successMsg, type: "success" });
      }
    } catch (err: any) {
      setFeedbackMessage({ text: err.message || "Failed to apply patch.", type: "error" });
    }
  };

  const handleRefineSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!refinePrompt.trim() || isRefining) return;

    setIsRefining(true);
    try {
      if (onRefineWithAI) {
        const updated = await onRefineWithAI(dashboard.id, refinePrompt);
        setDashboard(updated);
        setRefinePrompt("");
        setFeedbackMessage({ text: "Dashboard refined successfully with AI instructions.", type: "success" });
      } else {
        const updated = await api.post<Dashboard>(`/api/v1/dashboards/${dashboard.id}/refine`, {
          refinement_prompt: refinePrompt,
        });
        setDashboard(updated);
        setRefinePrompt("");
        setFeedbackMessage({ text: "Dashboard refined successfully with AI instructions.", type: "success" });
      }
    } catch (err: any) {
      setFeedbackMessage({ text: err.message || "Refinement failed.", type: "error" });
    } finally {
      setIsRefining(false);
    }
  };

  const fetchQualityScore = async () => {
    setIsLoadingQuality(true);
    setQualityModalOpen(true);
    try {
      const data = await api.get<DashboardQualityReport>(`/api/v1/dashboards/${dashboard.id}/quality`);
      setQualityReport(data);
    } catch {
      // Ignore
    } finally {
      setIsLoadingQuality(false);
    }
  };

  // Sort widgets by grid_y then grid_x for natural accessibility flow
  const sortedWidgets = [...dashboard.widgets].sort((a, b) => {
    if (a.grid_y === b.grid_y) {
      return a.grid_x - b.grid_x;
    }
    return a.grid_y - b.grid_y;
  });

  const dashboardTitle = dashboard.name;

  return (
    <div className="space-y-6">
      {/* Toast Feedback Notification */}
      {feedbackMessage && (
        <div
          className={cn(
            "fixed bottom-6 right-6 z-50 flex items-center gap-2 rounded-xl px-4 py-3 text-xs font-medium shadow-soft-lg transition-all animate-in fade-in slide-in-from-bottom-2",
            feedbackMessage.type === "success" && "bg-teal text-white",
            feedbackMessage.type === "error" && "bg-rose text-white",
            feedbackMessage.type === "info" && "bg-ink text-white"
          )}
          role="status"
          aria-live="polite"
        >
          <span>{feedbackMessage.text}</span>
        </div>
      )}

      {/* Dashboard Top Header */}
      <header className="rounded-2xl border border-border bg-surface p-5 md:p-6 shadow-soft">
        <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
          <div className="space-y-1.5">
            <div className="flex flex-wrap items-center gap-2.5">
              <h1 className="text-xl md:text-2xl font-bold tracking-tight text-ink">
                {dashboardTitle}
              </h1>
              <span
                className={cn(
                  "rounded-full px-2.5 py-0.5 text-[11px] font-semibold uppercase tracking-wider",
                  dashboard.status === "READY" && "bg-teal-soft text-teal border border-teal-border",
                  dashboard.status === "GENERATING" && "bg-amber-50 text-amber-700 border border-amber-200",
                  dashboard.status === "PARTIAL" && "bg-amber-100 text-amber-800",
                  dashboard.status === "FAILED" && "bg-rose/10 text-rose border border-rose/20"
                )}
              >
                {dashboard.status}
              </span>
            </div>
            {dashboard.description && (
              <p className="text-xs md:text-sm text-slate leading-relaxed max-w-3xl">
                {dashboard.description}
              </p>
            )}
            <div className="flex flex-wrap items-center gap-4 pt-1 text-[11px] text-slate">
              <span className="flex items-center gap-1.5">
                <Layers className="h-3.5 w-3.5 text-teal" />
                Dataset: <strong className="text-ink font-semibold">{dashboard.dataset_id}</strong>
              </span>
              <span className="flex items-center gap-1.5">
                <Calendar className="h-3.5 w-3.5 text-slate" />
                Version: <strong className="text-ink font-semibold">{dashboard.dataset_version_id}</strong>
              </span>
              <span>Updated: {new Date(dashboard.updated_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
            </div>
          </div>

          {/* Action Buttons Bar */}
          <div className="flex flex-wrap items-center gap-2 pt-2 md:pt-0">
            <button
              onClick={() => setShareModalOpen(true)}
              className="inline-flex items-center gap-1.5 rounded-xl border border-border bg-cloud-subtle px-3 py-2 text-xs font-medium text-slate hover:bg-cloud hover:text-ink transition-colors focus-visible:ring-2 focus-visible:ring-teal"
              title="Share dashboard securely with external viewers"
            >
              <Share2 className="h-3.5 w-3.5 text-teal" />
              <span>Share</span>
            </button>

            <button
              onClick={() => setExportModalOpen(true)}
              className="inline-flex items-center gap-1.5 rounded-xl border border-border bg-cloud-subtle px-3 py-2 text-xs font-medium text-slate hover:bg-cloud hover:text-ink transition-colors focus-visible:ring-2 focus-visible:ring-teal"
              title="Export as PDF, PNG, CSV, JSON or Print"
            >
              <Download className="h-3.5 w-3.5 text-teal" />
              <span>Export</span>
            </button>

            <button
              onClick={fetchQualityScore}
              className="inline-flex items-center gap-1.5 rounded-xl border border-border bg-cloud-subtle px-3 py-2 text-xs font-medium text-slate hover:bg-cloud hover:text-ink transition-colors focus-visible:ring-2 focus-visible:ring-teal"
              title="Inspect Explainable Quality Score"
            >
              <ShieldCheck className="h-3.5 w-3.5 text-teal" />
              <span>Quality Score</span>
            </button>

            <button
              onClick={handleRefresh}
              disabled={isRefreshing}
              className="inline-flex items-center gap-1.5 rounded-xl border border-border bg-cloud-subtle px-3 py-2 text-xs font-medium text-slate hover:bg-cloud hover:text-ink transition-colors focus-visible:ring-2 focus-visible:ring-teal disabled:opacity-50"
              title="Refresh all analytical computations"
            >
              <RefreshCw className={cn("h-3.5 w-3.5", isRefreshing && "animate-spin text-teal")} />
              <span>{isRefreshing ? "Refreshing..." : "Refresh"}</span>
            </button>

            <button
              onClick={() => setIsEditMode(!isEditMode)}
              className={cn(
                "inline-flex items-center gap-1.5 rounded-xl px-3.5 py-2 text-xs font-semibold transition-all focus-visible:ring-2 focus-visible:ring-teal",
                isEditMode
                  ? "bg-teal text-white shadow-soft"
                  : "border border-border bg-surface text-ink hover:bg-cloud"
              )}
            >
              {isEditMode ? (
                <>
                  <Check className="h-3.5 w-3.5" />
                  <span>Done Editing</span>
                </>
              ) : (
                <>
                  <Edit3 className="h-3.5 w-3.5" />
                  <span>Edit Layout</span>
                </>
              )}
            </button>
          </div>
        </div>

        {/* AI Natural Language Refinement Input */}
        <div className="mt-5 border-t border-border/80 pt-4">
          <form onSubmit={handleRefineSubmit} className="relative flex items-center">
            <div className="pointer-events-none absolute left-3.5 flex items-center text-teal">
              <Sparkles className="h-4 w-4" />
            </div>
            <input
              type="text"
              value={refinePrompt}
              onChange={(e) => setRefinePrompt(e.target.value)}
              placeholder="Ask AI to refine this dashboard (e.g., 'Change Revenue chart to horizontal bar', 'Remove region widget', 'Add monthly order trend')..."
              className="w-full rounded-xl border border-border bg-cloud-subtle/50 py-2.5 pl-10 pr-24 text-xs text-ink placeholder:text-slate/60 focus:border-teal focus:bg-surface focus:outline-none focus:ring-2 focus:ring-teal/20"
              disabled={isRefining}
            />
            <button
              type="submit"
              disabled={!refinePrompt.trim() || isRefining}
              className="absolute right-1.5 flex items-center gap-1.5 rounded-lg bg-teal px-3 py-1.5 text-xs font-semibold text-white shadow-soft hover:bg-teal-hover transition-colors disabled:opacity-50"
            >
              <Send className="h-3 w-3" />
              <span>{isRefining ? "Refining..." : "Refine"}</span>
            </button>
          </form>
        </div>
      </header>

      {/* Global & Categorical Dashboard Filters */}
      {dashboard.filters && dashboard.filters.length > 0 && (
        <DashboardFilterBar
          filters={dashboard.filters}
          activeFilters={activeFilters}
          onFilterChange={handleApplyFilter}
          onClearFilter={handleClearFilter}
        />
      )}

      {/* 12-Column Responsive Dashboard Grid */}
      {dashboard.widgets.length === 0 ? (
        <div className="rounded-2xl border-2 border-dashed border-border bg-surface/50 p-12 text-center">
          <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-2xl bg-teal-soft text-teal">
            <Layers className="h-6 w-6" />
          </div>
          <h3 className="mt-4 text-sm font-semibold text-ink">No widgets in this dashboard</h3>
          <p className="mt-1 text-xs text-slate max-w-sm mx-auto">
            Use the natural language refinement prompt above to add analytical components or generate a complete layout.
          </p>
        </div>
      ) : (
        <main
          className="grid grid-cols-1 md:grid-cols-12 gap-5"
          aria-label="Dashboard analytical components grid"
        >
          {sortedWidgets.map((widget) => {
            return (
              <DashboardWidgetCard
                key={widget.id}
                widget={widget}
                isEditMode={isEditMode}
                onRemove={() => handleRemoveWidget(widget.id)}
                onMove={(dir) => handleMoveWidget(widget.id, dir)}
                onResize={(w, h) => handleResizeWidget(widget.id, w, h)}
                onChangeChartType={(chart) => handleChangeChartType(widget.id, chart)}
                onInspectProvenance={(w) => setInspectWidget(w)}
              />
            );
          })}
        </main>
      )}

      {/* Provenance & Evidence Drawer Dialog */}
      <Dialog
        isOpen={!!inspectWidget}
        onClose={() => setInspectWidget(null)}
        title={inspectWidget ? `Analytical Provenance: ${inspectWidget.title}` : "Evidence"}
        description="Complete deterministic audit chain backing this widget."
      >
        {inspectWidget && (
          <div className="space-y-3.5 text-xs text-ink pt-2">
            <div className="rounded-xl bg-cloud p-3.5 space-y-2 border border-border">
              <div className="flex justify-between">
                <span className="text-slate font-medium">Widget Title:</span>
                <span className="font-semibold text-ink">{inspectWidget.title}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate font-medium">Widget ID:</span>
                <span className="font-mono text-[11px]">{inspectWidget.id}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate font-medium">Visualization Type:</span>
                <span className="rounded bg-teal-soft px-1.5 py-0.5 font-semibold text-teal text-[11px]">
                  {inspectWidget.chart_spec?.chart_type || inspectWidget.widget_type}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate font-medium">Analysis ID:</span>
                <span className="font-mono text-[11px] text-teal">{inspectWidget.analysis_id || "Direct Aggregation"}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate font-medium">Dataset / Version:</span>
                <span className="font-semibold">{dashboard.dataset_id} (v{dashboard.dataset_version_id})</span>
              </div>
            </div>

            {inspectWidget.chart_spec && (
              <div className="space-y-1.5">
                <label className="text-[11px] font-semibold uppercase tracking-wider text-slate">
                  Visualization Spec
                </label>
                <pre className="max-h-40 overflow-auto rounded-xl bg-slate-900 p-3 text-[11px] text-slate-100 font-mono">
                  {JSON.stringify(inspectWidget.chart_spec, null, 2)}
                </pre>
              </div>
            )}
          </div>
        )}
      </Dialog>

      {/* Explainable Quality Score Dialog */}
      <Dialog
        isOpen={qualityModalOpen}
        onClose={() => setQualityModalOpen(false)}
        title="Explainable Dashboard Quality Score"
        description="Deterministic evaluation score computed across widget coverage, diversity, data quality, and bounds."
      >
        {isLoadingQuality ? (
          <div className="py-8 text-center text-xs text-slate">
            <RefreshCw className="mx-auto h-5 w-5 animate-spin text-teal mb-2" />
            <span>Computing deterministic quality metrics...</span>
          </div>
        ) : qualityReport ? (
          <div className="space-y-4 pt-2">
            <div className="flex items-center justify-between rounded-xl bg-teal-soft p-4 border border-teal-border">
              <div>
                <div className="text-[11px] font-medium text-teal">Overall Quality Score</div>
                <div className="text-3xl font-bold text-teal tracking-tight">
                  {qualityReport.overall_score} <span className="text-sm font-normal text-teal/70">/ 100</span>
                </div>
              </div>
              <div className="text-right text-[11px] text-teal">
                <div>Valid Ratio: <strong>{(qualityReport.valid_widget_ratio * 100).toFixed(0)}%</strong></div>
                <div>Redundancy: <strong>{(qualityReport.redundancy_penalty * 100).toFixed(0)}%</strong></div>
              </div>
            </div>

            <div className="space-y-2 text-xs">
              <div className="flex justify-between py-1 border-b border-border">
                <span className="text-slate">Data Coverage Score</span>
                <span className="font-semibold text-ink">{(qualityReport.data_coverage_score * 100).toFixed(0)}%</span>
              </div>
              <div className="flex justify-between py-1 border-b border-border">
                <span className="text-slate">Visual Diversity Score</span>
                <span className="font-semibold text-ink">{(qualityReport.visual_diversity_score * 100).toFixed(0)}%</span>
              </div>
            </div>
          </div>
        ) : (
          <div className="py-6 text-center text-xs text-slate">
            Could not compute quality report.
          </div>
        )}
      </Dialog>

      {/* Phase 9 Export Modal */}
      <DashboardExportModal
        isOpen={exportModalOpen}
        onClose={() => setExportModalOpen(false)}
        dashboard={dashboard}
        activeFilters={activeFilters}
      />

      {/* Phase 9 Share Modal */}
      <DashboardShareModal
        isOpen={shareModalOpen}
        onClose={() => setShareModalOpen(false)}
        dashboard={dashboard}
      />
    </div>
  );
}

