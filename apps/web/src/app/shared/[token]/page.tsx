"use client";

import * as React from "react";
import { useParams } from "next/navigation";
import {
  Printer,
  ShieldCheck,
  Calendar,
  Layers,
  AlertCircle,
  Loader2,
  Lock,
  Camera,
  Radio,
  RefreshCw,
} from "lucide-react";
import {
  SharedDashboardViewResponse,
  DashboardWidget,
} from "@/types";
import { DashboardWidgetCard } from "@/components/dashboards/dashboard-widget";
import { DashboardFilterBar } from "@/components/dashboards/dashboard-filter-bar";
import { cn } from "@/lib/utils";

export default function SharedDashboardPage() {
  const params = useParams();
  const token = typeof params.token === "string" ? params.token : "";

  const [dashboardData, setDashboardData] = React.useState<SharedDashboardViewResponse | null>(null);
  const [isLoading, setIsLoading] = React.useState(true);
  const [isRefreshing, setIsRefreshing] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);
  const [activeFilters, setActiveFilters] = React.useState<Record<string, unknown>>({});

  const fetchSharedDashboard = React.useCallback(async () => {
    if (!token) return;
    setIsLoading(true);
    setError(null);
    try {
      const res = await fetch(`/api/v1/shared/dashboards/${token}`);
      if (!res.ok) {
        if (res.status === 404) {
          throw new Error("This shared dashboard link is invalid or has expired.");
        }
        throw new Error(`Failed to load shared dashboard (Status ${res.status}).`);
      }
      const data: SharedDashboardViewResponse = await res.json();
      setDashboardData(data);
    } catch (err) {
      setError((err as Error).message || "Unable to access shared dashboard.");
    } finally {
      setIsLoading(false);
    }
  }, [token]);

  React.useEffect(() => {
    fetchSharedDashboard();
  }, [fetchSharedDashboard]);

  const handleApplyFilter = async (columnName: string, value: unknown) => {
    const updatedFilters = { ...activeFilters, [columnName]: value };
    setActiveFilters(updatedFilters);

    if (dashboardData?.is_snapshot) {
      // In snapshot mode, filtering is local or read-only
      return;
    }

    // Refresh shared dashboard view with session filters
    setIsRefreshing(true);
    try {
      const res = await fetch(`/api/v1/shared/dashboards/${token}/refresh`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ filter_values: updatedFilters }),
      });
      if (res.ok) {
        const updated: SharedDashboardViewResponse = await res.json();
        setDashboardData(updated);
      }
    } catch {
      // ignore
    } finally {
      setIsRefreshing(false);
    }
  };

  const handleClearFilter = async (columnName: string) => {
    const copy = { ...activeFilters };
    delete copy[columnName];
    setActiveFilters(copy);

    if (dashboardData?.is_snapshot) return;

    setIsRefreshing(true);
    try {
      const res = await fetch(`/api/v1/shared/dashboards/${token}/refresh`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ filter_values: copy }),
      });
      if (res.ok) {
        const updated: SharedDashboardViewResponse = await res.json();
        setDashboardData(updated);
      }
    } catch {
      // ignore
    } finally {
      setIsRefreshing(false);
    }
  };

  if (isLoading) {
    return (
      <div className="flex min-h-screen flex-col items-center justify-center bg-cloud p-4">
        <div className="flex items-center gap-3 rounded-2xl border border-border bg-surface px-6 py-4 shadow-soft">
          <Loader2 className="h-5 w-5 animate-spin text-teal" />
          <span className="text-sm font-medium text-ink">Loading shared dashboard...</span>
        </div>
      </div>
    );
  }

  if (error || !dashboardData) {
    return (
      <div className="flex min-h-screen flex-col items-center justify-center bg-cloud p-4">
        <div className="max-w-md rounded-2xl border border-border bg-surface p-6 shadow-soft text-center space-y-4">
          <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-2xl bg-rose/10 text-rose">
            <AlertCircle className="h-6 w-6" />
          </div>
          <div className="space-y-1">
            <h2 className="text-lg font-bold text-ink">Dashboard Unavailable</h2>
            <p className="text-xs text-slate">{error || "This shared dashboard could not be loaded."}</p>
          </div>
          <p className="text-[11px] text-slate/80">
            The link may have expired, been revoked by the owner, or contains an incorrect security token.
          </p>
        </div>
      </div>
    );
  }

  // Filter widgets matching allowed viewer scope
  const widgets: DashboardWidget[] = (dashboardData.widgets || []).map((w: any) => ({
    ...w,
    dashboard_id: dashboardData.dashboard_id,
  }));

  const sortedWidgets = [...widgets].sort((a, b) => {
    if (a.grid_y === b.grid_y) return a.grid_x - b.grid_x;
    return a.grid_y - b.grid_y;
  });

  return (
    <div className="min-h-screen bg-cloud text-ink p-4 md:p-8">
      <div className="mx-auto max-w-7xl space-y-6">
        {/* Top Header Banner */}
        <header className="rounded-2xl border border-border bg-surface p-5 md:p-6 shadow-soft">
          <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
            <div className="space-y-1.5">
              <div className="flex flex-wrap items-center gap-2.5">
                <h1 className="text-xl md:text-2xl font-bold tracking-tight text-ink">
                  {dashboardData.title}
                </h1>
                <span className="flex items-center gap-1 rounded-full bg-teal-soft text-teal border border-teal-border px-2.5 py-0.5 text-[11px] font-semibold">
                  <Lock className="h-3 w-3" />
                  Read-Only
                </span>
                {dashboardData.is_snapshot ? (
                  <span className="flex items-center gap-1 rounded-full bg-sky-100 text-sky-800 border border-sky-200 px-2.5 py-0.5 text-[11px] font-semibold">
                    <Camera className="h-3 w-3" />
                    Snapshot
                  </span>
                ) : (
                  <span className="flex items-center gap-1 rounded-full bg-teal-soft/80 text-teal border border-teal-border px-2.5 py-0.5 text-[11px] font-semibold">
                    <Radio className="h-3 w-3" />
                    Live
                  </span>
                )}
              </div>
              {dashboardData.description && (
                <p className="text-xs md:text-sm text-slate leading-relaxed max-w-3xl">
                  {dashboardData.description}
                </p>
              )}
              <div className="flex flex-wrap items-center gap-4 pt-1 text-[11px] text-slate">
                <span className="flex items-center gap-1.5">
                  <Layers className="h-3.5 w-3.5 text-teal" />
                  Dataset: <strong className="text-ink font-semibold">{dashboardData.dataset_id}</strong>
                </span>
                <span className="flex items-center gap-1.5">
                  <Calendar className="h-3.5 w-3.5 text-slate" />
                  Version: <strong className="text-ink font-semibold">{dashboardData.dataset_version_id}</strong>
                </span>
                <span>
                  Updated: {new Date(dashboardData.updated_at).toLocaleDateString()}{" "}
                  {new Date(dashboardData.updated_at).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
                </span>
              </div>
            </div>

            {/* Print / Refresh Trigger */}
            <div className="flex items-center gap-2">
              {!dashboardData.is_snapshot && (
                <button
                  type="button"
                  onClick={fetchSharedDashboard}
                  disabled={isRefreshing}
                  className="flex items-center gap-1.5 rounded-xl border border-border bg-cloud-subtle px-3 py-2 text-xs font-semibold text-ink hover:bg-cloud transition-colors disabled:opacity-50"
                  title="Refresh live data"
                >
                  <RefreshCw className={cn("h-3.5 w-3.5", isRefreshing && "animate-spin text-teal")} />
                  <span>{isRefreshing ? "Refreshing..." : "Refresh"}</span>
                </button>
              )}
              <button
                type="button"
                onClick={() => window.print()}
                className="flex items-center gap-1.5 rounded-xl bg-teal px-4 py-2 text-xs font-semibold text-white shadow-soft hover:bg-teal-hover transition-colors"
                title="Print or export as PDF"
              >
                <Printer className="h-3.5 w-3.5" />
                <span>Print / PDF</span>
              </button>
            </div>
          </div>
        </header>

        {/* Filter Bar (Only showing allowed filters) */}
        {dashboardData.filters && dashboardData.filters.length > 0 && (
          <DashboardFilterBar
            filters={dashboardData.filters as any}
            activeFilters={activeFilters}
            onFilterChange={handleApplyFilter}
            onClearFilter={handleClearFilter}
          />
        )}


        {/* Widgets Grid */}
        <section
          className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4"
          aria-label="Shared Dashboard Analytics"
        >
          {sortedWidgets.map((widget) => (
            <div
              key={widget.id}
              className={cn(
                "transition-all",
                widget.grid_w === 4 && "md:col-span-2 lg:col-span-4",
                widget.grid_w === 3 && "md:col-span-2 lg:col-span-3",
                widget.grid_w === 2 && "md:col-span-2 lg:col-span-2",
                widget.grid_w === 1 && "col-span-1"
              )}
            >
              <DashboardWidgetCard
                widget={widget}
                isEditMode={false}
              />
            </div>
          ))}
        </section>

        {/* Footer */}
        <footer className="flex flex-col sm:flex-row items-center justify-between border-t border-border pt-4 text-[11px] text-slate gap-2">
          <div className="flex items-center gap-1.5">
            <ShieldCheck className="h-4 w-4 text-teal" />
            <span>InsightFlow AI Grounded Analytical Specification</span>
          </div>
          <div>
            Powered by InsightFlow AI Deterministic Engine
          </div>
        </footer>
      </div>
    </div>
  );
}
