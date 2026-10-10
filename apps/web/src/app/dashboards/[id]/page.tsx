"use client";

import * as React from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { ArrowLeft, LayoutDashboard } from "lucide-react";
import { AppShell } from "@/components/shell/app-shell";
import { DashboardView } from "@/components/dashboards/dashboard-view";
import { LoadingState } from "@/components/states/loading-state";
import { ErrorState } from "@/components/states/error-state";
import { api } from "@/lib/api-client";
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
      const data = await api.get<Dashboard>(`/api/v1/dashboards/${dashboardId}`);
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
    try {
      await api.delete(`/api/v1/dashboards/${id}`);
      router.push("/dashboards");
    } catch {
      // Ignore
    }
  };

  return (
    <AppShell>
      <div className="space-y-6">
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
