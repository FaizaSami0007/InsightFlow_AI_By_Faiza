"use client";

import * as React from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { ArrowLeft, LayoutDashboard } from "lucide-react";
import { AppShell } from "@/components/shell/app-shell";
import { DashboardView } from "@/components/dashboards/dashboard-view";
import { LoadingState } from "@/components/states/loading-state";
import { ErrorState } from "@/components/states/error-state";
import { Dashboard } from "@/types";

export default function DashboardDetailPage() {
  const params = useParams();
  const router = useRouter();
  const dashboardId = params.id as string;

  const [dashboard, setDashboard] = React.useState<Dashboard | null>(null);
  const [isLoading, setIsLoading] = React.useState(true);
  const [error, setError] = React.useState<string | null>(null);

  const fetchDashboard = React.useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const token = localStorage.getItem("token");
      const res = await fetch(`/api/v1/dashboards/${dashboardId}`, {
        headers: token ? { Authorization: `Bearer ${token}` } : {},
      });
      if (!res.ok) {
        if (res.status === 404) throw new Error("Dashboard not found.");
        if (res.status === 403) throw new Error("Access denied to this dashboard.");
        throw new Error("Failed to load dashboard.");
      }
      const data: Dashboard = await res.json();
      setDashboard(data);
    } catch (err: any) {
      setError(err.message || "An unexpected error occurred.");
    } finally {
      setIsLoading(false);
    }
  }, [dashboardId]);

  React.useEffect(() => {
    if (dashboardId) {
      fetchDashboard();
    }
  }, [dashboardId, fetchDashboard]);

  const handleDelete = async (id: string) => {
    const token = localStorage.getItem("token");
    const res = await fetch(`/api/v1/dashboards/${id}`, {
      method: "DELETE",
      headers: token ? { Authorization: `Bearer ${token}` } : {},
    });
    if (res.ok) {
      router.push("/dashboards");
    }
  };

  return (
    <AppShell>
      <div className="p-6 md:p-8 max-w-7xl mx-auto space-y-6">
        {/* Breadcrumb / Back Link */}
        <div className="flex items-center gap-2">
          <Link
            href="/dashboards"
            className="inline-flex items-center gap-1.5 text-xs font-medium text-slate hover:text-teal transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-teal rounded-lg px-2 py-1 -ml-2"
          >
            <ArrowLeft className="h-3.5 w-3.5" />
            <span>All Dashboards</span>
          </Link>
        </div>

        {isLoading ? (
          <div className="py-20">
            <LoadingState
              title="Loading Dashboard"
              description="Fetching deterministic analytics and visualization specifications..."
            />
          </div>
        ) : error ? (
          <div className="py-20">
            <ErrorState
              title="Dashboard Unavailable"
              message={error}
              onRetry={fetchDashboard}
            />
          </div>
        ) : dashboard ? (
          <DashboardView
            initialDashboard={dashboard}
            onRefresh={fetchDashboard}
            onDelete={handleDelete}
          />
        ) : null}
      </div>
    </AppShell>
  );
}
