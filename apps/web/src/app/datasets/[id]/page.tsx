"use client";

import React, { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { Dataset, DatasetProfile, DatasetVersion } from "@/types";
import { api } from "@/lib/api-client";
import { AppShell } from "@/components/shell/app-shell";
import { TabContent, TabList, TabTrigger, Tabs } from "@/components/ui/tabs";
import { Select } from "@/components/ui/select";
import { LoadingState } from "@/components/states/loading-state";
import { ErrorState } from "@/components/states/error-state";
import { OverviewTab } from "@/components/profiling/overview-tab";
import { SchemaTab } from "@/components/profiling/schema-tab";
import { StatisticsTab } from "@/components/profiling/statistics-tab";
import { QualityTab } from "@/components/profiling/quality-tab";
import { SemanticsTab } from "@/components/profiling/semantics-tab";
import { AnalyticsTab } from "@/components/profiling/analytics-tab";
import { AIAnalystView } from "@/components/analyst/ai-analyst-view";

export default function DatasetDetailPage() {
  const params = useParams();
  const router = useRouter();
  const datasetId = params.id as string;

  const [dataset, setDataset] = useState<Dataset | null>(null);
  const [selectedVersionId, setSelectedVersionId] = useState<string>("");
  const [profile, setProfile] = useState<DatasetProfile | null>(null);
  const [activeTab, setActiveTab] = useState<string>("overview");

  const [isLoadingDataset, setIsLoadingDataset] = useState(true);
  const [isLoadingProfile, setIsLoadingProfile] = useState(false);
  const [isProfiling, setIsProfiling] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // 1. Fetch Dataset & Versions
  const loadDataset = React.useCallback(async () => {
    setIsLoadingDataset(true);
    setError(null);
    try {
      const data = await api.get<Dataset>(`/api/v1/datasets/${datasetId}`);
      setDataset(data);
      if (data.versions && data.versions.length > 0) {
        const initialVersionId = data.latest_version?.id || data.versions[0].id;
        setSelectedVersionId(initialVersionId);
      }
    } catch (err) {
      setError((err as Error).message || "Failed to load dataset.");
    } finally {
      setIsLoadingDataset(false);
    }
  }, [datasetId]);

  useEffect(() => {
    if (datasetId) {
      loadDataset();
    }
  }, [datasetId, loadDataset]);

  // 2. Fetch or trigger profile for selected version
  const loadProfile = React.useCallback(async (versionId: string, force = false) => {
    if (!versionId) return;
    if (force) setIsProfiling(true);
    else setIsLoadingProfile(true);

    try {
      const endpoint = force
        ? `/api/v1/datasets/${datasetId}/versions/${versionId}/profile?force=true`
        : `/api/v1/datasets/${datasetId}/versions/${versionId}/profile`;
      const data = force
        ? await api.post<DatasetProfile>(endpoint)
        : await api.get<DatasetProfile>(endpoint);
      setProfile(data);
    } catch (err) {
      console.error("Profile load error:", err);
    } finally {
      setIsLoadingProfile(false);
      setIsProfiling(false);
    }
  }, [datasetId]);

  useEffect(() => {
    if (selectedVersionId) {
      loadProfile(selectedVersionId);
    }
  }, [selectedVersionId, loadProfile]);

  if (isLoadingDataset) {
    return (
      <AppShell>
        <div className="flex h-96 items-center justify-center">
          <LoadingState title="Loading Dataset" description="Retrieving schema, lineage, and latest profile..." />
        </div>
      </AppShell>
    );
  }

  if (error || !dataset) {
    return (
      <AppShell>
        <div className="p-8 max-w-2xl mx-auto">
          <ErrorState
            title="Dataset Not Found"
            message={error || "Could not retrieve the requested dataset."}
            onRetry={loadDataset}
          />
          <div className="mt-4 text-center">
            <Link href="/datasets" className="text-sm text-teal hover:text-teal-hover font-medium">
              &larr; Return to Datasets
            </Link>
          </div>
        </div>
      </AppShell>
    );
  }

  const versions = dataset.versions || [];
  const currentVersion =
    versions.find((v) => v.id === selectedVersionId) ||
    dataset.latest_version ||
    versions[0];

  const versionOptions = versions.map((v) => ({
    value: v.id,
    label: `v${v.version_number} — ${v.file_name} (${new Date(v.created_at).toLocaleDateString()})`,
  }));

  const tabItems = [
    { id: "overview", label: "Overview" },
    { id: "schema", label: "Schema" },
    { id: "statistics", label: "Statistics" },
    { id: "quality", label: "Data Quality" },
    { id: "semantics", label: "Semantics" },
    { id: "analytics", label: "Analytics" },
    { id: "analyst", label: "AI Analyst" },
  ];

  return (
    <AppShell>
      <div className="p-6 md:p-8 max-w-7xl mx-auto space-y-6">
        {/* Breadcrumb & Top Bar */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="space-y-1">
            <nav className="flex items-center gap-2 text-xs text-slate">
              <Link href="/datasets" className="hover:text-ink transition-colors">
                Datasets
              </Link>
              <span>/</span>
              <span className="text-ink font-semibold truncate max-w-xs">{dataset.name}</span>
            </nav>
            <h1 className="text-lg sm:text-xl lg:text-2xl font-bold tracking-tight text-ink">{dataset.name}</h1>
            {dataset.description && (
              <p className="text-xs sm:text-sm text-slate max-w-3xl">{dataset.description}</p>
            )}
          </div>

          {/* Version Switcher */}
          {versions.length > 1 && (
            <div className="w-full sm:w-72">
              <label className="text-xs font-semibold text-slate-400 uppercase tracking-wider block mb-1">
                Dataset Version
              </label>
              <Select
                options={versionOptions}
                value={selectedVersionId}
                onChange={(e) => setSelectedVersionId(e.target.value)}
                className="text-xs"
              />
            </div>
          )}
        </div>

        {/* Tab Navigation */}
        <Tabs value={activeTab} onValueChange={setActiveTab}>
          <TabList>
            {tabItems.map((t) => (
              <TabTrigger key={t.id} value={t.id}>
                {t.label}
              </TabTrigger>
            ))}
          </TabList>

          {/* Tab Contents */}
          {isLoadingProfile ? (
            <div className="py-12 flex justify-center">
              <LoadingState title="Computing Profile" description="Executing Polars and DuckDB statistical analyzers..." />
            </div>
          ) : (
            <div className="pt-2">
              <TabContent value="overview">
                {currentVersion && (
                  <OverviewTab
                    dataset={dataset}
                    version={currentVersion}
                    profile={profile}
                    isProfiling={isProfiling}
                    onTriggerProfile={() => loadProfile(selectedVersionId, true)}
                  />
                )}
              </TabContent>
              <TabContent value="schema">
                <SchemaTab profile={profile} />
              </TabContent>
              <TabContent value="statistics">
                <StatisticsTab profile={profile} />
              </TabContent>
              <TabContent value="quality">
                <QualityTab profile={profile} />
              </TabContent>
              <TabContent value="semantics">
                <SemanticsTab
                  datasetId={dataset.id}
                  versionId={selectedVersionId}
                  profile={profile}
                  onRefresh={() => loadProfile(selectedVersionId, false)}
                />
              </TabContent>
              <TabContent value="analytics">
                <AnalyticsTab
                  datasetId={dataset.id}
                  versionId={selectedVersionId}
                  profile={profile}
                />
              </TabContent>
              <TabContent value="analyst">
                <AIAnalystView
                  initialDatasetId={dataset.id}
                  initialVersionId={selectedVersionId}
                />
              </TabContent>
            </div>
          )}
        </Tabs>
      </div>
    </AppShell>
  );
}
