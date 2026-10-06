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
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
        <Card className="p-4 bg-surface border-border shadow-soft">
          <div className="text-xs font-medium text-slate uppercase tracking-wider">Total Rows</div>
          <div className="text-2xl font-bold text-ink mt-1">
            {profile?.row_count?.toLocaleString() ?? version.row_count?.toLocaleString() ?? "—"}
          </div>
          <div className="text-xs text-slate mt-1">Records observed</div>
        </Card>

        <Card className="p-4 bg-surface border-border shadow-soft">
          <div className="text-xs font-medium text-slate uppercase tracking-wider">Columns</div>
          <div className="text-2xl font-bold text-ink mt-1">
            {profile?.column_count ?? version.column_count ?? "—"}
          </div>
          <div className="text-xs text-slate mt-1">Features indexed</div>
        </Card>

        <Card className="p-4 bg-surface border-border shadow-soft">
          <div className="text-xs font-medium text-slate uppercase tracking-wider">Format</div>
          <div className="text-2xl font-bold text-ink mt-1">
            {version.file_format}
          </div>
          <div className="text-xs text-slate mt-1">{formatBytes(version.file_size)}</div>
        </Card>

        <Card className="p-4 bg-surface border-border shadow-soft">
          <div className="text-xs font-medium text-slate uppercase tracking-wider">Quality Score</div>
          <div className="flex items-center gap-2 mt-1">
            <span className="text-2xl font-bold text-ink">
              {qualityScore !== null ? `${qualityScore}%` : "—"}
            </span>
            {qualityScore !== null && (
              <Badge variant={getGradeBadgeVariant(qualityGrade)}>
                Grade {qualityGrade}
              </Badge>
            )}
          </div>
          <div className="text-xs text-slate mt-1">Explainable index</div>
        </Card>

        <Card className="p-4 bg-surface border-border shadow-soft">
          <div className="text-xs font-medium text-slate uppercase tracking-wider">Duplicates</div>
          <div className="text-2xl font-bold text-ink mt-1">
            {profile?.quality_report?.duplicate_summary?.duplicate_rows ?? 0}
          </div>
          <div className="text-xs text-slate mt-1">
            {profile?.quality_report?.duplicate_summary?.duplicate_percentage ?? 0}% duplicate rate
          </div>
        </Card>

        <Card className="p-4 bg-surface border-border shadow-soft">
          <div className="text-xs font-medium text-slate uppercase tracking-wider">Profile Time</div>
          <div className="text-2xl font-bold text-ink mt-1">
            {profile?.duration_ms ? `${profile.duration_ms} ms` : "—"}
          </div>
          <div className="text-xs text-slate mt-1">Deterministic speed</div>
        </Card>
      </div>

      {/* Lineage & System Info Card */}
      <Card className="p-6 bg-surface border-border shadow-soft">
        <h3 className="text-sm font-semibold text-ink mb-4">Dataset Provenance & Metadata</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 text-sm">
          <div className="space-y-3">
            <div className="flex justify-between border-b border-border pb-2">
              <span className="text-slate">Dataset ID</span>
              <span className="font-mono text-ink font-medium">{dataset.id}</span>
            </div>
            <div className="flex justify-between border-b border-border pb-2">
              <span className="text-slate">Version ID</span>
              <span className="font-mono text-ink font-medium">{version.id}</span>
            </div>
            <div className="flex justify-between border-b border-border pb-2">
              <span className="text-slate">Status</span>
              <Badge variant={version.status === "READY" ? "teal" : "amber"}>
                {version.status}
              </Badge>
            </div>
          </div>

          <div className="space-y-3">
            <div className="flex justify-between border-b border-border pb-2">
              <span className="text-slate">Uploaded At</span>
              <span className="text-ink">{new Date(version.created_at).toLocaleString()}</span>
            </div>
            <div className="flex justify-between border-b border-border pb-2">
              <span className="text-slate">Last Profiled</span>
              <span className="text-ink">
                {profile?.created_at ? new Date(profile.created_at).toLocaleString() : "Not profiled"}
              </span>
            </div>
            <div className="flex justify-between border-b border-border pb-2">
              <span className="text-slate">Analytical Engine</span>
              <span className="text-teal font-medium">DuckDB &amp; Polars (Active)</span>
            </div>
          </div>
        </div>
      </Card>
    </div>
  );
}
