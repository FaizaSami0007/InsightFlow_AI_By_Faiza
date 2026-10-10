"use client";

import React, { useState, useEffect, useCallback } from "react";
import Link from "next/link";
import {
  LineChart,
  Database,
  Layers,
  Sparkles,
  ArrowRight,
  Upload,
  RefreshCw,
  Clock,
  CheckCircle2,
  ShieldCheck,
} from "lucide-react";
import { Dataset, DatasetListResponse, DatasetProfile } from "@/types";
import { api, ApiError } from "@/lib/api-client";
import { useAuthStore } from "@/stores/use-auth-store";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { PageHero } from "@/components/ui/page-hero";
import { LoadingState } from "@/components/states/loading-state";
import { EmptyState } from "@/components/states/empty-state";
import { ErrorState } from "@/components/states/error-state";
import { AnalyticsTab } from "@/components/profiling/analytics-tab";

export function AnalyticsWorkspace() {
  const { isAuthenticated, isInitializing } = useAuthStore();

  const [datasets, setDatasets] = useState<Dataset[]>([]);
  const [selectedDatasetId, setSelectedDatasetId] = useState<string>("");
  const [selectedVersionId, setSelectedVersionId] = useState<string>("");
  const [profile, setProfile] = useState<DatasetProfile | null>(null);

  const [isLoadingDatasets, setIsLoadingDatasets] = useState(true);
  const [isLoadingProfile, setIsLoadingProfile] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // 1. Fetch Datasets
  const fetchDatasets = useCallback(async () => {
    if (!isAuthenticated) {
      setIsLoadingDatasets(false);
      return;
    }
    setIsLoadingDatasets(true);
    setError(null);
    try {
      const response = await api.get<DatasetListResponse>("/api/v1/datasets?page=1&page_size=50");
      setDatasets(response.items);
      if (response.items.length > 0 && !selectedDatasetId) {
        const first = response.items[0];
        setSelectedDatasetId(first.id);
        const versionId = first.latest_version?.id || (first.versions && first.versions[0]?.id) || "";
        setSelectedVersionId(versionId);
      }
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to load datasets.");
    } finally {
      setIsLoadingDatasets(false);
    }
  }, [isAuthenticated, selectedDatasetId]);

  useEffect(() => {
    if (isAuthenticated) {
      fetchDatasets();
    } else if (!isInitializing) {
      setIsLoadingDatasets(false);
    }
  }, [isAuthenticated, isInitializing, fetchDatasets]);

  // 2. Load Profile when dataset/version changes
  const loadProfile = useCallback(async (datasetId: string, versionId: string) => {
    if (!datasetId || !versionId) return;
    setIsLoadingProfile(true);
    try {
      const data = await api.get<DatasetProfile>(
        `/api/v1/datasets/${datasetId}/versions/${versionId}/profile`
      );
      setProfile(data);
    } catch {
      // If not yet profiled, attempt to trigger deterministic profile
      try {
        const generated = await api.post<DatasetProfile>(
          `/api/v1/datasets/${datasetId}/versions/${versionId}/profile`
        );
        setProfile(generated);
      } catch (genErr) {
        console.error("Profile generation error:", genErr);
        setProfile(null);
      }
    } finally {
      setIsLoadingProfile(false);
    }
  }, []);

  useEffect(() => {
    if (selectedDatasetId && selectedVersionId) {
      loadProfile(selectedDatasetId, selectedVersionId);
    }
  }, [selectedDatasetId, selectedVersionId, loadProfile]);

  const handleDatasetChange = (datasetId: string) => {
    setSelectedDatasetId(datasetId);
    const target = datasets.find((d) => d.id === datasetId);
    if (target) {
      const vId = target.latest_version?.id || (target.versions && target.versions[0]?.id) || "";
      setSelectedVersionId(vId);
    }
  };

  const selectedDataset = datasets.find((d) => d.id === selectedDatasetId);

  if (isInitializing || (isLoadingDatasets && datasets.length === 0)) {
    return (
      <LoadingState
        title="Loading Analytics Engine"
        description="Connecting to DuckDB analytical runtime and indexing dataset catalog..."
      />
    );
  }

  if (!isAuthenticated) {
    return (
      <Card className="max-w-xl mx-auto my-12 border-border shadow-soft">
        <CardHeader className="text-center pb-2">
          <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-2xl bg-teal-soft text-teal mb-2">
            <LineChart className="h-6 w-6" />
          </div>
          <CardTitle>Authentication Required</CardTitle>
          <p className="text-xs text-slate mt-1">
            Please sign in to execute high-performance deterministic SQL aggregations, correlation matrices, and time-series models.
          </p>
        </CardHeader>
        <div className="flex justify-center gap-3 p-6 pt-2">
          <Link href="/login">
            <Button variant="primary">Sign In</Button>
          </Link>
          <Link href="/register">
            <Button variant="outline">Create Account</Button>
          </Link>
        </div>
      </Card>
    );
  }

  if (error) {
    return <ErrorState message={error} onRetry={fetchDatasets} />;
  }

  if (datasets.length === 0) {
    return (
      <EmptyState
        icon={<Database className="h-10 w-10 text-slate" />}
        title="No datasets available for analysis"
        description="Upload your first tabular CSV or Parquet file to run verified DuckDB aggregations, distributions, and correlation matrices."
        action={
          <Link href="/datasets">
            <Button variant="primary" size="sm" leftIcon={<Upload className="h-3.5 w-3.5" />}>
              Go to Datasets & Upload
            </Button>
          </Link>
        }
      />
    );
  }

  return (
    <div className="space-y-6">
      {/* Top Header & Dataset Switcher via PageHero */}
      <PageHero
        variant="gradient"
        phaseBadge="Phase 7 Active"
        subtitle="DuckDB + Polars High-Performance Analytics"
        icon={<LineChart className="h-5 w-5" />}
        title="Deterministic Analytics Engine"
        badge={
          <Badge variant="teal" dot className="bg-teal-500/20 text-teal-300 border-teal-400/30 text-[10px] sm:text-xs shrink-0">
            DuckDB + Polars
          </Badge>
        }
        description="Verified statistical calculations, multidimensional group-bys, percent-changes, and Tukey outlier filters."
        statusBadge={
          <>
            <ShieldCheck className="w-4 h-4 text-teal-300 shrink-0" />
            <span>Grounded Calculation Chain</span>
          </>
        }
        actions={
          <div className="flex items-center gap-2 sm:gap-3 flex-wrap w-full xl:w-auto min-w-0">
            <div className="flex items-center gap-2 min-w-0 flex-1 sm:flex-initial">
              <label className="text-xs font-semibold text-teal-200 whitespace-nowrap shrink-0">Dataset:</label>
              <select
                value={selectedDatasetId}
                onChange={(e) => handleDatasetChange(e.target.value)}
                className="bg-white/10 text-white text-xs rounded-xl border border-white/20 px-3 py-1.5 focus:ring-2 focus:ring-teal outline-none font-medium flex-1 sm:w-56 max-w-full truncate"
              >
                {datasets.length === 0 ? (
                  <option value="" disabled className="text-slate-500 bg-white">
                    No datasets available
                  </option>
                ) : (
                  datasets.map((d) => (
                    <option key={d.id} value={d.id} className="text-[#172033] bg-white font-medium">
                      {d.name} (v{d.version_count})
                    </option>
                  ))
                )}
              </select>
            </div>

            {selectedDataset && (
              <Link href={`/datasets/${selectedDataset.id}`} className="shrink-0">
                <Button variant="outline" size="sm" className="bg-white/10 hover:bg-white/20 text-white border-white/20 text-xs whitespace-nowrap">
                  View Schema Lineage &rarr;
                </Button>
              </Link>
            )}
          </div>
        }
      />

      {/* Analytics Workspace Main Area */}
      {selectedDatasetId && selectedVersionId ? (
        isLoadingProfile && !profile ? (
          <LoadingState
            title="Loading Column Profiles"
            description="Extracting analytical schema and data distribution metadata..."
          />
        ) : (
          <AnalyticsTab
            datasetId={selectedDatasetId}
            versionId={selectedVersionId}
            profile={profile}
          />
        )
      ) : (
        <div className="p-12 text-center text-slate bg-surface rounded-2xl border border-border shadow-soft">
          Please select a dataset above to begin analysis.
        </div>
      )}
    </div>
  );
}
