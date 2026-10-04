"use client";

import React, { useState } from "react";
import { Dataset, DashboardPlan, Dashboard } from "@/types";
import { apiRequest } from "@/lib/api-client";
import {
  Sparkles,
  LayoutGrid,
  AlertCircle,
  TrendingUp,
  Activity,
  Layers,
  ArrowRight,
  Loader2,
} from "lucide-react";
import { Dialog } from "@/components/ui/dialog";

interface DashboardGeneratorModalProps {
  isOpen: boolean;
  onClose: () => void;
  datasets: Dataset[];
  selectedDatasetId?: string;
  onDashboardCreated: (dashboard: Dashboard) => void;
}

export function DashboardGeneratorModal({
  isOpen,
  onClose,
  datasets,
  selectedDatasetId,
  onDashboardCreated,
}: DashboardGeneratorModalProps) {
  const [datasetId, setDatasetId] = useState<string>(selectedDatasetId || datasets[0]?.id || "");
  const [purpose, setPurpose] = useState<string>("sales");
  const [intent, setIntent] = useState<string>("");
  const [isGenerating, setIsGenerating] = useState<boolean>(false);
  const [isPreviewing, setIsPreviewing] = useState<boolean>(false);
  const [previewPlan, setPreviewPlan] = useState<DashboardPlan | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const currentDataset = datasets.find((d) => d.id === datasetId);
  const latestVersion = currentDataset?.latest_version;

  const handlePreviewPlan = async () => {
    if (!datasetId || !latestVersion) {
      setErrorMessage("Please select a valid dataset version.");
      return;
    }

    setIsPreviewing(true);
    setErrorMessage(null);

    try {
      const plan = await apiRequest<DashboardPlan>("/api/v1/dashboards/plan-preview", {
        method: "POST",
        body: JSON.stringify({
          dataset_id: datasetId,
          dataset_version_id: latestVersion.id,
          purpose: purpose || undefined,
          intent: intent || undefined,
        }),
      });
      setPreviewPlan(plan);
    } catch (err: unknown) {
      setErrorMessage((err as Error).message || "Failed to preview dashboard plan.");
    } finally {
      setIsPreviewing(false);
    }
  };

  const handleCommitGeneration = async () => {
    if (!datasetId || !latestVersion) return;

    setIsGenerating(true);
    setErrorMessage(null);

    try {
      const dashboard = await apiRequest<Dashboard>("/api/v1/dashboards/generate", {
        method: "POST",
        body: JSON.stringify({
          dataset_id: datasetId,
          dataset_version_id: latestVersion.id,
          purpose: purpose || undefined,
          intent: intent || undefined,
        }),
      });
      onDashboardCreated(dashboard);
      onClose();
    } catch (err: unknown) {
      setErrorMessage((err as Error).message || "Failed to generate dashboard.");
    } finally {
      setIsGenerating(false);
    }
  };

  return (
    <Dialog
      isOpen={isOpen}
      onClose={onClose}
      title="AI Automated Dashboard Generation"
      description="Plan, validate, and build a deterministic analytical dashboard grounded in dataset semantics."
    >
      <div className="space-y-4 text-xs text-[#172033]">
        {errorMessage && (
          <div className="flex items-center gap-2 p-3 bg-red-50 text-red-700 text-xs rounded-lg border border-red-200">
            <AlertCircle className="w-4 h-4 shrink-0" />
            <span>{errorMessage}</span>
          </div>
        )}

        {/* Dataset Selector */}
        <div>
          <label className="block font-semibold mb-1 text-[#172033]">1. Select Dataset</label>
          <select
            value={datasetId}
            onChange={(e) => {
              setDatasetId(e.target.value);
              setPreviewPlan(null);
            }}
            className="w-full bg-[#F7F9FC] border border-[#E3E8EF] rounded-lg px-3 py-2 text-xs font-medium text-[#172033] focus:outline-none focus:border-[#0F766E]"
          >
            {datasets.map((d) => (
              <option key={d.id} value={d.id}>
                {d.name} (v{d.latest_version?.version_number || 1})
              </option>
            ))}
          </select>
        </div>

        {/* Purpose Presets */}
        <div>
          <label className="block font-semibold mb-1 text-[#172033]">2. Analytical Purpose</label>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
            {[
              { id: "sales", label: "Sales Performance", icon: TrendingUp },
              { id: "operations", label: "Operations", icon: Activity },
              { id: "overview", label: "Executive Summary", icon: LayoutGrid },
              { id: "quality", label: "Data Quality", icon: Layers },
            ].map((p) => {
              const Icon = p.icon;
              const isSelected = purpose === p.id;
              return (
                <button
                  key={p.id}
                  type="button"
                  onClick={() => {
                    setPurpose(p.id);
                    setPreviewPlan(null);
                  }}
                  className={`flex flex-col items-center justify-center p-3 rounded-lg border transition-all text-center gap-1.5 ${
                    isSelected
                      ? "bg-[#E6F4F1] border-[#0F766E] text-[#0F766E] font-semibold"
                      : "bg-[#F7F9FC] border-[#E3E8EF] text-[#536176] hover:bg-slate-100"
                  }`}
                >
                  <Icon className="w-4 h-4" />
                  <span className="text-[11px]">{p.label}</span>
                </button>
              );
            })}
          </div>
        </div>

        {/* Natural Language Prompt */}
        <div>
          <label className="block font-semibold mb-1 text-[#172033]">
            3. Custom Intent (Optional)
          </label>
          <input
            type="text"
            placeholder="e.g. Focus on regional revenue and monthly unit sales trends"
            value={intent}
            onChange={(e) => {
              setIntent(e.target.value);
              setPreviewPlan(null);
            }}
            className="w-full bg-[#F7F9FC] border border-[#E3E8EF] rounded-lg px-3 py-2 text-xs text-[#172033] focus:outline-none focus:border-[#0F766E]"
          />
        </div>

        {/* Plan Preview Section */}
        {previewPlan && (
          <div className="p-3 bg-slate-50 border border-[#E3E8EF] rounded-lg space-y-2">
            <div className="flex items-center justify-between">
              <span className="font-bold text-xs text-[#172033]">
                Planned Dashboard: &quot;{previewPlan.title}&quot;
              </span>
              <span className="text-[11px] px-2 py-0.5 bg-[#E6F4F1] text-[#0F766E] font-semibold rounded">
                {previewPlan.widgets.length} Widgets Planned
              </span>
            </div>
            <p className="text-[11px] text-[#536176]">{previewPlan.reasoning_summary}</p>

            <div className="space-y-1.5 mt-2 max-h-40 overflow-y-auto pr-1">
              {previewPlan.widgets.map((w, idx) => (
                <div
                  key={idx}
                  className="flex items-center justify-between p-2 bg-white rounded border border-[#E3E8EF] text-[11px]"
                >
                  <div className="flex items-center gap-2">
                    <span className="w-4 h-4 flex items-center justify-center bg-slate-100 rounded text-[10px] font-bold">
                      {idx + 1}
                    </span>
                    <span className="font-semibold">{w.title}</span>
                  </div>
                  <div className="flex items-center gap-2 text-[#536176]">
                    <span className="uppercase text-[10px] px-1 bg-slate-100 rounded">
                      {w.preferred_chart_type || w.widget_type}
                    </span>
                    <span>{w.grid_w} col</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Modal Actions */}
        <div className="flex items-center justify-end gap-2 pt-2 border-t border-[#E3E8EF]">
          <button
            type="button"
            onClick={onClose}
            className="px-4 py-2 text-xs font-semibold text-[#536176] hover:bg-slate-100 rounded-lg transition-colors"
          >
            Cancel
          </button>

          {!previewPlan ? (
            <button
              type="button"
              onClick={handlePreviewPlan}
              disabled={isPreviewing || !datasetId}
              className="flex items-center gap-1.5 px-4 py-2 text-xs font-semibold bg-[#F7F9FC] text-[#172033] border border-[#E3E8EF] hover:bg-slate-100 rounded-lg transition-colors disabled:opacity-50"
            >
              {isPreviewing ? (
                <>
                  <Loader2 className="w-3.5 h-3.5 animate-spin" />
                  <span>Analyzing Dataset...</span>
                </>
              ) : (
                <>
                  <span>Preview Plan</span>
                  <ArrowRight className="w-3.5 h-3.5" />
                </>
              )}
            </button>
          ) : null}

          <button
            type="button"
            onClick={handleCommitGeneration}
            disabled={isGenerating || !datasetId}
            className="flex items-center gap-1.5 px-4 py-2 text-xs font-semibold bg-[#0F766E] text-white hover:bg-[#0d655e] rounded-lg transition-colors shadow-sm disabled:opacity-50"
          >
            {isGenerating ? (
              <>
                <Loader2 className="w-3.5 h-3.5 animate-spin" />
                <span>Generating Dashboard...</span>
              </>
            ) : (
              <>
                <Sparkles className="w-3.5 h-3.5" />
                <span>Generate Dashboard</span>
              </>
            )}
          </button>
        </div>
      </div>
    </Dialog>
  );
}
