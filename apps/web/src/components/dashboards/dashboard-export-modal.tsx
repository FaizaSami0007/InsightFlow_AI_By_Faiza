"use client";

import * as React from "react";
import {
  Download,
  FileText,
  Image as ImageIcon,
  Table,
  Printer,
  FileCode,
  Check,
  AlertCircle,
  Loader2,
  Sliders,
  Compass,
} from "lucide-react";
import { Dialog } from "@/components/ui/dialog";
import {
  Dashboard,
  ExportFormat,
  ExportRequest,
  ExportResponse,
} from "@/types";
import { api, ApiError } from "@/lib/api-client";
import { cn } from "@/lib/utils";

interface DashboardExportModalProps {
  isOpen: boolean;
  onClose: () => void;
  dashboard: Dashboard;
  activeFilters?: Record<string, unknown>;
}

export function DashboardExportModal({
  isOpen,
  onClose,
  dashboard,
  activeFilters = {},
}: DashboardExportModalProps) {
  const [format, setFormat] = React.useState<ExportFormat>("pdf");
  const [pageSize, setPageSize] = React.useState<"A4" | "Letter">("A4");
  const [orientation, setOrientation] = React.useState<"landscape" | "portrait">("landscape");
  const [includeProvenance, setIncludeProvenance] = React.useState(true);
  const [includeFilters, setIncludeFilters] = React.useState(true);
  const [titleOverride, setTitleOverride] = React.useState(dashboard.name);
  const [selectedWidgetId, setSelectedWidgetId] = React.useState<string>("");

  const [isLoading, setIsLoading] = React.useState(false);
  const [loadingStep, setLoadingStep] = React.useState<string>("");
  const [exportResult, setExportResult] = React.useState<ExportResponse | null>(null);
  const [errorMessage, setErrorMessage] = React.useState<string | null>(null);

  React.useEffect(() => {
    setTitleOverride(dashboard.name);
    setExportResult(null);
    setErrorMessage(null);
  }, [dashboard, isOpen]);

  const handlePrint = () => {
    onClose();
    setTimeout(() => {
      window.print();
    }, 300);
  };

  const handleExport = async () => {
    if (format === "csv" && !selectedWidgetId && dashboard.widgets.length > 0) {
      // Default to first widget if none selected
      setSelectedWidgetId(dashboard.widgets[0].id);
    }

    setIsLoading(true);
    setErrorMessage(null);
    setExportResult(null);
    setLoadingStep(
      format === "pdf"
        ? "Preparing PDF report & layout..."
        : format === "png"
        ? "Rendering high-resolution snapshot..."
        : format === "csv"
        ? "Extracting validated tabular data..."
        : "Exporting dashboard specification..."
    );

    try {
      const payload: ExportRequest = {
        format,
        page_size: pageSize,
        orientation,
        include_provenance: includeProvenance,
        include_filters: includeFilters,
        title_override: titleOverride.trim() || dashboard.name,
        filter_values: activeFilters,
        widget_id: format === "csv" && selectedWidgetId ? selectedWidgetId : undefined,
      };

      const result = await api.post<ExportResponse>(
        `/api/v1/dashboards/${dashboard.id}/exports`,
        payload
      );

      setExportResult(result);
      setLoadingStep("Export ready.");

      // Automatically trigger download
      if (result.download_url) {
        const ext = format === "pdf" ? "pdf" : format === "png" ? "png" : format === "csv" ? "csv" : "json";
        const sanitizedTitle = (titleOverride || dashboard.name)
          .toLowerCase()
          .replace(/[^a-z0-9_-]/g, "_");
        const filename = `${sanitizedTitle}.${ext}`;
        await api.download(result.download_url, filename);
      }
    } catch (err) {
      const errorMsg =
        err instanceof ApiError
          ? err.message
          : "Export could not be completed. Please try again.";
      setErrorMessage(errorMsg);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <Dialog
      isOpen={isOpen}
      onClose={onClose}
      title="Export Dashboard"
      description="Export validated analytics and visual specs into presentation-ready reports."
      className="max-w-xl"
    >
      <div className="space-y-6">
        {/* Quick Print Banner */}
        <div className="flex items-center justify-between border-b border-border pb-3">
          <span className="text-xs text-slate">Choose your preferred export format below:</span>
          <button
            onClick={handlePrint}
            className="flex items-center gap-1.5 rounded-xl border border-border bg-cloud-subtle px-3 py-1.5 text-xs font-semibold text-ink hover:bg-cloud transition-colors"
            title="Open browser print dialog"
          >
            <Printer className="h-3.5 w-3.5 text-teal" />
            <span>Quick Print</span>
          </button>
        </div>


        {/* Format Selector Grid */}
        <div className="space-y-2">
          <label className="text-xs font-semibold uppercase tracking-wider text-slate">
            Select Format
          </label>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5">
            {[
              {
                id: "pdf" as ExportFormat,
                label: "PDF Report",
                desc: "Multi-page A4/Letter",
                icon: FileText,
              },
              {
                id: "png" as ExportFormat,
                label: "PNG Image",
                desc: "High-res snapshot",
                icon: ImageIcon,
              },
              {
                id: "csv" as ExportFormat,
                label: "CSV Data",
                desc: "Tabular result data",
                icon: Table,
              },
              {
                id: "json" as ExportFormat,
                label: "JSON Spec",
                desc: "Dashboard state",
                icon: FileCode,
              },
            ].map((f) => {
              const Icon = f.icon;
              const isSelected = format === f.id;
              return (
                <button
                  key={f.id}
                  type="button"
                  onClick={() => setFormat(f.id)}
                  className={cn(
                    "flex flex-col items-start rounded-xl border p-3 text-left transition-all",
                    isSelected
                      ? "border-teal bg-teal-soft/40 shadow-soft"
                      : "border-border bg-surface hover:border-slate/40 hover:bg-cloud-subtle"
                  )}
                >
                  <div className="flex items-center justify-between w-full">
                    <Icon
                      className={cn(
                        "h-4 w-4",
                        isSelected ? "text-teal" : "text-slate"
                      )}
                    />
                    {isSelected && <Check className="h-3.5 w-3.5 text-teal" />}
                  </div>
                  <span className="mt-2 text-xs font-bold text-ink">{f.label}</span>
                  <span className="text-[10px] text-slate">{f.desc}</span>
                </button>
              );
            })}
          </div>
        </div>

        {/* Configuration Options */}
        <div className="space-y-4 rounded-xl border border-border bg-cloud-subtle/30 p-4">
          <div className="space-y-1.5">
            <label className="text-xs font-medium text-ink">Report Title</label>
            <input
              type="text"
              value={titleOverride}
              onChange={(e) => setTitleOverride(e.target.value)}
              placeholder="Report Title"
              className="w-full rounded-xl border border-border bg-surface px-3 py-2 text-xs text-ink placeholder:text-slate focus:border-teal focus:outline-none focus:ring-2 focus:ring-teal/20"
            />
          </div>

          {/* PDF Specific Options */}
          {format === "pdf" && (
            <div className="grid grid-cols-2 gap-3 pt-2">
              <div className="space-y-1.5">
                <label className="text-xs font-medium text-ink">Page Size</label>
                <select
                  value={pageSize}
                  onChange={(e) => setPageSize(e.target.value as "A4" | "Letter")}
                  className="w-full rounded-xl border border-border bg-surface px-3 py-2 text-xs text-ink focus:border-teal focus:outline-none focus:ring-2 focus:ring-teal/20"
                >
                  <option value="A4">A4 (210 x 297 mm)</option>
                  <option value="Letter">Letter (8.5 x 11 in)</option>
                </select>
              </div>
              <div className="space-y-1.5">
                <label className="text-xs font-medium text-ink">Orientation</label>
                <select
                  value={orientation}
                  onChange={(e) => setOrientation(e.target.value as "landscape" | "portrait")}
                  className="w-full rounded-xl border border-border bg-surface px-3 py-2 text-xs text-ink focus:border-teal focus:outline-none focus:ring-2 focus:ring-teal/20"
                >
                  <option value="landscape">Landscape (Recommended)</option>
                  <option value="portrait">Portrait</option>
                </select>
              </div>
            </div>
          )}

          {/* CSV Target Widget Selector */}
          {format === "csv" && (
            <div className="space-y-1.5 pt-2">
              <label className="text-xs font-medium text-ink">Target Widget for Data Export</label>
              <select
                value={selectedWidgetId}
                onChange={(e) => setSelectedWidgetId(e.target.value)}
                className="w-full rounded-xl border border-border bg-surface px-3 py-2 text-xs text-ink focus:border-teal focus:outline-none focus:ring-2 focus:ring-teal/20"
              >
                <option value="">All Available Tabular Results</option>
                {dashboard.widgets.map((w) => (
                  <option key={w.id} value={w.id}>
                    {w.title} ({w.widget_type})
                  </option>
                ))}
              </select>
            </div>
          )}

          {/* Toggles */}
          <div className="flex flex-wrap items-center gap-6 pt-2 border-t border-border/60">
            <label className="flex items-center gap-2 text-xs text-ink cursor-pointer">
              <input
                type="checkbox"
                checked={includeProvenance}
                onChange={(e) => setIncludeProvenance(e.target.checked)}
                className="rounded border-border text-teal focus:ring-teal"
              />
              <Compass className="h-3.5 w-3.5 text-teal" />
              <span>Include Analytical Provenance & Audit Trail</span>
            </label>
            <label className="flex items-center gap-2 text-xs text-ink cursor-pointer">
              <input
                type="checkbox"
                checked={includeFilters}
                onChange={(e) => setIncludeFilters(e.target.checked)}
                className="rounded border-border text-teal focus:ring-teal"
              />
              <Sliders className="h-3.5 w-3.5 text-slate" />
              <span>Include Active Filter State</span>
            </label>
          </div>
        </div>

        {/* Loading Indicator */}
        {isLoading && (
          <div className="flex items-center gap-3 rounded-xl bg-teal-soft/30 border border-teal-border p-3 text-xs text-teal animate-pulse">
            <Loader2 className="h-4 w-4 animate-spin text-teal" />
            <span className="font-semibold">{loadingStep}</span>
          </div>
        )}

        {/* Success Notice */}
        {exportResult && !isLoading && (
          <div className="flex items-center justify-between rounded-xl bg-teal-soft/40 border border-teal-border p-3 text-xs text-ink">
            <div className="flex items-center gap-2">
              <Check className="h-4 w-4 text-teal" />
              <span>
                Export complete! ({((exportResult.file_size_bytes || 0) / 1024).toFixed(1)} KB)
              </span>
            </div>
            <button
              onClick={() => {
                const ext = format === "pdf" ? "pdf" : format === "png" ? "png" : format === "csv" ? "csv" : "json";
                const sanitizedTitle = (titleOverride || dashboard.name)
                  .toLowerCase()
                  .replace(/[^a-z0-9_-]/g, "_");
                api.download(exportResult.download_url, `${sanitizedTitle}.${ext}`);
              }}
              className="font-semibold text-teal hover:underline"
            >
              Re-download
            </button>
          </div>
        )}

        {/* Error Notice */}
        {errorMessage && !isLoading && (
          <div className="flex items-start gap-2 rounded-xl bg-rose/10 border border-rose/20 p-3 text-xs text-rose">
            <AlertCircle className="h-4 w-4 shrink-0 mt-0.5" />
            <div>
              <p className="font-semibold">Export failed</p>
              <p className="text-[11px] opacity-90 mt-0.5">{errorMessage}</p>
            </div>
          </div>
        )}

        {/* Action Buttons */}
        <div className="flex items-center justify-end gap-2.5 border-t border-border pt-4">
          <button
            type="button"
            onClick={onClose}
            className="rounded-xl border border-border bg-surface px-4 py-2 text-xs font-semibold text-slate hover:bg-cloud transition-colors"
          >
            Close
          </button>
          <button
            type="button"
            onClick={handleExport}
            disabled={isLoading}
            className="flex items-center gap-2 rounded-xl bg-teal px-5 py-2 text-xs font-semibold text-white shadow-soft hover:bg-teal-hover transition-colors disabled:opacity-50"
          >
            {isLoading ? (
              <>
                <Loader2 className="h-4 w-4 animate-spin" />
                <span>Generating...</span>
              </>
            ) : (
              <>
                <Download className="h-4 w-4" />
                <span>Export {format.toUpperCase()}</span>
              </>
            )}
          </button>
        </div>
      </div>
    </Dialog>
  );
}
