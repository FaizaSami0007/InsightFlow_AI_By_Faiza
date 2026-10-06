"use client";

import React from "react";
import { DatasetProfile } from "@/types";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

interface QualityTabProps {
  profile: DatasetProfile | null;
}

export function QualityTab({ profile }: QualityTabProps) {
  const quality = profile?.quality_report;

  if (!profile || !quality) {
    return (
      <div className="p-8 text-center text-slate bg-surface rounded-xl border border-border shadow-soft">
        No quality audit available. Run the profiler to analyze data quality.
      </div>
    );
  }

  const getSeverityBadgeVariant = (severity: string): "danger" | "amber" | "blue" | "outline" => {
    switch (severity) {
      case "ERROR":
        return "danger";
      case "WARNING":
        return "amber";
      case "INFO":
        return "blue";
      default:
        return "outline";
    }
  };

  const getScoreColor = (score: number) => {
    if (score >= 90) return "text-teal";
    if (score >= 80) return "text-blue";
    if (score >= 70) return "text-amber";
    return "text-danger";
  };

  return (
    <div className="space-y-6">
      {/* Quality Score Hero Card */}
      <Card className="p-6 bg-surface border-border shadow-soft">
        <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-6">
          <div className="flex items-center gap-6">
            <div className="flex flex-col items-center justify-center w-24 h-24 rounded-2xl bg-cloud border border-border shadow-sm">
              <span className={`text-4xl font-extrabold ${getScoreColor(quality.overall_score)}`}>
                {quality.overall_score}
              </span>
              <span className="text-xs font-semibold text-slate uppercase tracking-widest mt-0.5">
                Grade {quality.grade}
              </span>
            </div>
            <div>
              <h3 className="text-lg font-bold text-ink">Deterministic Data Quality Score</h3>
              <p className="text-sm text-slate mt-1">
                Calculated through transparent penalty weights across missingness, duplicates, constant values, and outliers.
              </p>
              <div className="flex items-center gap-2 mt-2">
                <Badge variant={quality.total_issues === 0 ? "teal" : "amber"}>
                  {quality.total_issues} Active {quality.total_issues === 1 ? "Notice" : "Notices"}
                </Badge>
              </div>
            </div>
          </div>
        </div>
      </Card>

      {/* Breakdown Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Missingness */}
        <Card className="p-4 bg-surface border-border shadow-soft">
          <div className="text-xs font-semibold text-slate uppercase tracking-wider">Missingness</div>
          <div className="text-2xl font-bold text-ink mt-1">
            {quality.missing_summary.average_null_percentage}%
          </div>
          <p className="text-xs text-slate mt-1">Average null rate across columns</p>
          <div className="mt-3 pt-3 border-t border-border space-y-1 text-xs text-slate">
            <div className="flex justify-between">
              <span>0% Nulls:</span>
              <span className="text-ink font-mono font-medium">{quality.missing_summary.buckets.zero_missing || 0} cols</span>
            </div>
            <div className="flex justify-between">
              <span>&gt;20% High Nulls:</span>
              <span className="text-amber font-mono font-medium">
                {(quality.missing_summary.buckets.high_20_to_50 || 0) + (quality.missing_summary.buckets.critical_over_50 || 0)} cols
              </span>
            </div>
          </div>
        </Card>

        {/* Duplicates */}
        <Card className="p-4 bg-surface border-border shadow-soft">
          <div className="text-xs font-semibold text-slate uppercase tracking-wider">Duplicates</div>
          <div className="text-2xl font-bold text-ink mt-1">
            {quality.duplicate_summary.duplicate_rows.toLocaleString()}
          </div>
          <p className="text-xs text-slate mt-1">
            {quality.duplicate_summary.duplicate_percentage}% duplicate record rate
          </p>
          <div className="mt-3 pt-3 border-t border-border space-y-1 text-xs text-slate">
            <div className="flex justify-between">
              <span>Status:</span>
              <span className={quality.duplicate_summary.duplicate_rows > 0 ? "text-amber font-semibold" : "text-teal font-semibold"}>
                {quality.duplicate_summary.duplicate_rows > 0 ? "Duplicates Present" : "Unique Rows"}
              </span>
            </div>
          </div>
        </Card>

        {/* Constant Columns */}
        <Card className="p-4 bg-surface border-border shadow-soft">
          <div className="text-xs font-semibold text-slate uppercase tracking-wider">Constant Columns</div>
          <div className="text-2xl font-bold text-ink mt-1">
            {quality.constant_columns.length}
          </div>
          <p className="text-xs text-slate mt-1">Columns with &le;1 distinct value</p>
          <div className="mt-3 pt-3 border-t border-border space-y-1 text-xs text-slate">
            <div className="flex justify-between">
              <span>Variance:</span>
              <span className="text-ink font-mono font-medium">
                {quality.constant_columns.length > 0 ? "Zero variance detected" : "All columns varied"}
              </span>
            </div>
          </div>
        </Card>

        {/* Outlier Rate */}
        <Card className="p-4 bg-surface border-border shadow-soft">
          <div className="text-xs font-semibold text-slate uppercase tracking-wider">Statistical Outliers</div>
          <div className="text-2xl font-bold text-ink mt-1">
            {quality.outlier_summary.columns_with_outliers}
          </div>
          <p className="text-xs text-slate mt-1">Numeric columns with Tukey IQR outliers</p>
          <div className="mt-3 pt-3 border-t border-border space-y-1 text-xs text-slate">
            <div className="flex justify-between">
              <span>Avg Outlier Rate:</span>
              <span className="text-ink font-mono font-medium">{quality.outlier_summary.average_outlier_percentage}%</span>
            </div>
          </div>
        </Card>
      </div>

      {/* Actionable Warnings / Quality Feed */}
      <Card className="p-6 bg-surface border-border shadow-soft">
        <h4 className="text-sm font-semibold text-ink mb-4">Quality Warnings &amp; Observations</h4>
        {quality.warnings.length === 0 ? (
          <div className="p-4 text-center text-sm text-teal bg-teal-soft rounded-xl border border-teal-border">
            ✓ No critical quality anomalies or high-severity warnings detected.
          </div>
        ) : (
          <div className="space-y-3">
            {quality.warnings.map((warn, idx) => (
              <div
                key={idx}
                className="p-4 rounded-xl border border-border bg-cloud flex items-start justify-between gap-4"
              >
                <div className="space-y-1">
                  <div className="flex items-center gap-2">
                    <Badge variant={getSeverityBadgeVariant(warn.severity)}>
                      {warn.severity}
                    </Badge>
                    <span className="text-xs font-mono text-slate">{warn.rule}</span>
                  </div>
                  <p className="text-sm text-ink mt-1">{warn.message}</p>
                </div>
              </div>
            ))}
          </div>
        )}
      </Card>
    </div>
  );
}
