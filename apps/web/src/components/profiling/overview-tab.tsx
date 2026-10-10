"use client";

import React from "react";
import { Dataset, DatasetProfile, DatasetVersion } from "@/types";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";

interface OverviewTabProps {
  dataset: Dataset;
  version: DatasetVersion;
  profile: DatasetProfile | null;
  isProfiling: boolean;
  onTriggerProfile: () => void;
}

export function OverviewTab({
  dataset,
  version,
  profile,
  isProfiling,
  onTriggerProfile,
}: OverviewTabProps) {
  const qualityScore = profile?.quality_report?.overall_score ?? null;
  const qualityGrade = profile?.quality_report?.grade ?? "N/A";

  const formatBytes = (bytes: number) => {
    if (bytes === 0) return "0 B";
    const k = 1024;
    const sizes = ["B", "KB", "MB", "GB"];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + " " + sizes[i];
  };

  const getGradeBadgeVariant = (grade: string): "teal" | "blue" | "amber" | "danger" | "outline" => {
    switch (grade) {
      case "A":
        return "teal";
      case "B":
        return "blue";
      case "C":
        return "amber";
      case "D":
      case "F":
        return "danger";
      default:
        return "outline";
    }
  };

  return (
    <div className="space-y-6">
      {/* Top Header Actions */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 p-4 rounded-xl bg-surface border border-border shadow-soft">
        <div>
          <h2 className="text-lg font-semibold text-ink">{dataset.name}</h2>
          <p className="text-sm text-slate">
            Version {version.version_number} &bull; File: {version.file_name} &bull; SHA-256:{" "}
            <span className="font-mono text-xs text-slate">{version.checksum.slice(0, 12)}...</span>
          </p>
        </div>
        <div className="flex items-center gap-3">
          <Button
            variant="outline"
            size="sm"
            onClick={onTriggerProfile}
            isLoading={isProfiling}
          >
            {profile ? "Refresh Profile" : "Run Profiler"}
          </Button>
        </div>
      </div>

      {/* KPI Cards Grid */}
      <div className="grid grid-cols-2 md:grid-cols-3 xl:grid-cols-6 gap-3.5 sm:gap-4">
        <Card className="p-4 bg-surface border-border shadow-soft flex flex-col justify-between">
          <div>
            <div className="text-xs font-medium text-slate uppercase tracking-wider">Total Rows</div>
            <div className="text-2xl font-bold text-ink mt-1 tracking-tight">
              {profile?.row_count?.toLocaleString() ?? version.row_count?.toLocaleString() ?? "—"}
            </div>
          </div>
          <div className="text-xs text-slate mt-2 truncate">Records observed</div>
        </Card>

        <Card className="p-4 bg-surface border-border shadow-soft flex flex-col justify-between">
          <div>
            <div className="text-xs font-medium text-slate uppercase tracking-wider">Columns</div>
            <div className="text-2xl font-bold text-ink mt-1 tracking-tight">
              {profile?.column_count ?? version.column_count ?? "—"}
            </div>
          </div>
          <div className="text-xs text-slate mt-2 truncate">Features indexed</div>
        </Card>

        <Card className="p-4 bg-surface border-border shadow-soft flex flex-col justify-between">
          <div>
            <div className="text-xs font-medium text-slate uppercase tracking-wider">Format</div>
            <div className="text-2xl font-bold text-ink mt-1 tracking-tight uppercase">
              {version.file_format}
            </div>
          </div>
          <div className="text-xs text-slate mt-2 truncate">{formatBytes(version.file_size)}</div>
        </Card>

        <Card className="p-4 bg-surface border-border shadow-soft flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between gap-1">
              <span className="text-xs font-medium text-slate uppercase tracking-wider">Quality</span>
              {qualityGrade && (
                <Badge variant={getGradeBadgeVariant(qualityGrade)} className="text-[10px] px-1.5 py-0 shrink-0 font-semibold">
                  Grade {qualityGrade}
                </Badge>
              )}
            </div>
            <div className="text-2xl font-bold text-ink mt-1 tracking-tight">
              {qualityScore !== null ? `${qualityScore}%` : "—"}
            </div>
          </div>
          <div className="text-xs text-slate mt-2 truncate">Explainable index</div>
        </Card>

        <Card className="p-4 bg-surface border-border shadow-soft flex flex-col justify-between">
          <div>
            <div className="text-xs font-medium text-slate uppercase tracking-wider">Duplicates</div>
            <div className="text-2xl font-bold text-ink mt-1 tracking-tight">
              {profile?.quality_report?.duplicate_summary?.duplicate_rows?.toLocaleString() ?? 0}
            </div>
          </div>
          <div className="text-xs text-slate mt-2 truncate">
            {profile?.quality_report?.duplicate_summary?.duplicate_percentage ?? 0}% duplicate rate
          </div>
        </Card>

        <Card className="p-4 bg-surface border-border shadow-soft flex flex-col justify-between">
          <div>
            <div className="text-xs font-medium text-slate uppercase tracking-wider">Profile Time</div>
            <div className="flex items-baseline gap-1 mt-1">
              <span className="text-2xl font-bold text-ink tracking-tight">
                {profile?.duration_ms ?? "—"}
              </span>
              {profile?.duration_ms !== undefined && (
                <span className="text-xs font-medium text-slate">ms</span>
              )}
            </div>
          </div>
          <div className="text-xs text-slate mt-2 truncate">Deterministic speed</div>
        </Card>
      </div>

      {/* Lineage & System Info Card */}
      <Card className="p-5 sm:p-6 bg-surface border-border shadow-soft">
        <h3 className="text-sm font-semibold text-ink mb-4">Dataset Provenance & Metadata</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 text-sm">
          <div className="space-y-3">
            <div className="flex items-center justify-between border-b border-border pb-2 gap-2">
              <span className="text-slate shrink-0">Dataset ID</span>
              <span className="font-mono text-xs sm:text-sm text-ink font-medium truncate" title={dataset.id}>
                {dataset.id}
              </span>
            </div>
            <div className="flex items-center justify-between border-b border-border pb-2 gap-2">
              <span className="text-slate shrink-0">Version ID</span>
              <span className="font-mono text-xs sm:text-sm text-ink font-medium truncate" title={version.id}>
                {version.id}
              </span>
            </div>
            <div className="flex items-center justify-between border-b border-border pb-2">
              <span className="text-slate">Status</span>
              <Badge variant={version.status === "READY" ? "teal" : "amber"}>
                {version.status}
              </Badge>
            </div>
          </div>

          <div className="space-y-3">
            <div className="flex items-center justify-between border-b border-border pb-2">
              <span className="text-slate">Uploaded At</span>
              <span className="text-ink text-xs sm:text-sm">{new Date(version.created_at).toLocaleString()}</span>
            </div>
            <div className="flex items-center justify-between border-b border-border pb-2">
              <span className="text-slate">Last Profiled</span>
              <span className="text-ink text-xs sm:text-sm">
                {profile?.created_at ? new Date(profile.created_at).toLocaleString() : "Not profiled"}
              </span>
            </div>
            <div className="flex items-center justify-between border-b border-border pb-2">
              <span className="text-slate">Analytical Engine</span>
              <span className="text-teal font-medium text-xs sm:text-sm">DuckDB &amp; Polars (Active)</span>
            </div>
          </div>
        </div>
      </Card>
    </div>
  );
}
