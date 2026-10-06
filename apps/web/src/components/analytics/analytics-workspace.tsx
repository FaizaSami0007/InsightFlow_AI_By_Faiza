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
} from "lucide-react";
import { Dataset, DatasetListResponse, DatasetProfile } from "@/types";
import { api, ApiError } from "@/lib/api-client";
import { useAuthStore } from "@/stores/use-auth-store";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
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
      {/* Top Header & Dataset Switcher */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 p-5 rounded-2xl bg-surface border border-border shadow-soft">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-2xl font-bold tracking-tight text-ink flex items-center gap-2">
              <LineChart className="h-6 w-6 text-teal" />
              Deterministic Analytics Engine
            </h1>
            <Badge variant="teal" dot>
              DuckDB + Polars
            </Badge>
          </div>
          <p className="text-xs text-slate mt-0.5">
            Verified statistical calculations, multidimensional group-bys, percent-changes, and Tukey outlier filters.
          </p>
        </div>

        {/* Dataset & Version Selector */}
        <div className="flex items-center gap-3 flex-wrap">
          <div className="flex items-center gap-2">
            <label className="text-xs font-semibold text-slate">Active Dataset:</label>
            <select
              value={selectedDatasetId}
              onChange={(e) => handleDatasetChange(e.target.value)}
              className="bg-surface text-ink text-xs rounded-xl border border-border px-3 py-2 focus:ring-2 focus:ring-teal outline-none font-medium"
            >
              {datasets.map((d) => (
                <option key={d.id} value={d.id}>
                  {d.name} (v{d.version_count})
                </option>
              ))}
            </select>
          </div>

          {selectedDataset && (
            <Link href={`/datasets/${selectedDataset.id}`}>
              <Button variant="outline" size="sm" className="text-xs">
                View Schema Lineage &rarr;
              </Button>
            </Link>
          )}
        </div>
      </div>

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
