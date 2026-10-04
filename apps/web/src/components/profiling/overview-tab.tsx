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
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 p-4 rounded-xl bg-slate-900/60 border border-slate-800">
        <div>
          <h2 className="text-lg font-semibold text-slate-100">{dataset.name}</h2>
          <p className="text-sm text-slate-400">
            Version {version.version_number} &bull; File: {version.file_name} &bull; SHA-256:{" "}
            <span className="font-mono text-xs text-slate-500">{version.checksum.slice(0, 12)}...</span>
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
        <Card className="p-4 bg-slate-900/40 border-slate-800">
          <div className="text-xs font-medium text-slate-400 uppercase tracking-wider">Total Rows</div>
          <div className="text-2xl font-bold text-slate-100 mt-1">
            {profile?.row_count?.toLocaleString() ?? version.row_count?.toLocaleString() ?? "—"}
          </div>
          <div className="text-xs text-slate-500 mt-1">Records observed</div>
        </Card>

        <Card className="p-4 bg-slate-900/40 border-slate-800">
          <div className="text-xs font-medium text-slate-400 uppercase tracking-wider">Columns</div>
          <div className="text-2xl font-bold text-slate-100 mt-1">
            {profile?.column_count ?? version.column_count ?? "—"}
          </div>
          <div className="text-xs text-slate-500 mt-1">Features indexed</div>
        </Card>

        <Card className="p-4 bg-slate-900/40 border-slate-800">
          <div className="text-xs font-medium text-slate-400 uppercase tracking-wider">Format</div>
          <div className="text-2xl font-bold text-slate-100 mt-1">
            {version.file_format}
          </div>
          <div className="text-xs text-slate-500 mt-1">{formatBytes(version.file_size)}</div>
        </Card>

        <Card className="p-4 bg-slate-900/40 border-slate-800">
          <div className="text-xs font-medium text-slate-400 uppercase tracking-wider">Quality Score</div>
          <div className="flex items-center gap-2 mt-1">
            <span className="text-2xl font-bold text-slate-100">
              {qualityScore !== null ? `${qualityScore}%` : "—"}
            </span>
            {qualityScore !== null && (
              <Badge variant={getGradeBadgeVariant(qualityGrade)}>
                Grade {qualityGrade}
              </Badge>
            )}
          </div>
          <div className="text-xs text-slate-500 mt-1">Explainable index</div>
        </Card>

        <Card className="p-4 bg-slate-900/40 border-slate-800">
          <div className="text-xs font-medium text-slate-400 uppercase tracking-wider">Duplicates</div>
          <div className="text-2xl font-bold text-slate-100 mt-1">
            {profile?.quality_report?.duplicate_summary?.duplicate_rows ?? 0}
          </div>
          <div className="text-xs text-slate-500 mt-1">
            {profile?.quality_report?.duplicate_summary?.duplicate_percentage ?? 0}% duplicate rate
          </div>
        </Card>

        <Card className="p-4 bg-slate-900/40 border-slate-800">
          <div className="text-xs font-medium text-slate-400 uppercase tracking-wider">Profile Time</div>
          <div className="text-2xl font-bold text-slate-100 mt-1">
            {profile?.duration_ms ? `${profile.duration_ms} ms` : "—"}
          </div>
          <div className="text-xs text-slate-500 mt-1">Deterministic speed</div>
        </Card>
      </div>

      {/* Lineage & System Info Card */}
      <Card className="p-6 bg-slate-900/40 border-slate-800">
        <h3 className="text-sm font-semibold text-slate-200 mb-4">Dataset Provenance & Metadata</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 text-sm">
          <div className="space-y-3">
            <div className="flex justify-between border-b border-slate-800 pb-2">
              <span className="text-slate-400">Dataset ID</span>
              <span className="font-mono text-slate-200">{dataset.id}</span>
            </div>
            <div className="flex justify-between border-b border-slate-800 pb-2">
              <span className="text-slate-400">Version ID</span>
              <span className="font-mono text-slate-200">{version.id}</span>
            </div>
            <div className="flex justify-between border-b border-slate-800 pb-2">
              <span className="text-slate-400">Status</span>
              <Badge variant={version.status === "READY" ? "teal" : "amber"}>
                {version.status}
              </Badge>
            </div>
          </div>

          <div className="space-y-3">
            <div className="flex justify-between border-b border-slate-800 pb-2">
              <span className="text-slate-400">Uploaded At</span>
              <span className="text-slate-200">{new Date(version.created_at).toLocaleString()}</span>
            </div>
            <div className="flex justify-between border-b border-slate-800 pb-2">
              <span className="text-slate-400">Last Profiled</span>
              <span className="text-slate-200">
                {profile?.created_at ? new Date(profile.created_at).toLocaleString() : "Not profiled"}
              </span>
            </div>
            <div className="flex justify-between border-b border-slate-800 pb-2">
              <span className="text-slate-400">Analytical Engine</span>
              <span className="text-emerald-400 font-medium">DuckDB &amp; Polars (Active)</span>
            </div>
          </div>
        </div>
      </Card>
    </div>
  );
}
