"use client";

import React, { useState, useMemo } from "react";
import { DatasetProfile, SemanticColumn, SemanticRole } from "@/types";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Select } from "@/components/ui/select";
import { Button } from "@/components/ui/button";
import { api } from "@/lib/api-client";
import { cn } from "@/lib/utils";
import {
  Hash,
  Layers,
  KeyRound,
  Calendar,
  CircleDollarSign,
  Pencil,
  CheckCircle2,
  HelpCircle,
  Search,
  Sparkles,
  SlidersHorizontal,
} from "lucide-react";

interface SemanticsTabProps {
  datasetId: string;
  versionId: string;
  profile: DatasetProfile | null;
  onRefresh: () => void;
}

const ROLE_OPTIONS = [
  { value: "MEASURE", label: "Measure (Numeric / Metric)" },
  { value: "DIMENSION", label: "Dimension (Category / Grouping)" },
  { value: "IDENTIFIER", label: "Identifier (Key / ID)" },
  { value: "DATE", label: "Date" },
  { value: "DATETIME", label: "DateTime" },
  { value: "BOOLEAN", label: "Boolean Flag" },
  { value: "TEXT", label: "Freeform Text" },
  { value: "UNKNOWN", label: "Unknown / Unclassified" },
];

export function SemanticsTab({
  datasetId,
  versionId,
  profile,
  onRefresh,
}: SemanticsTabProps) {
  const semanticCols = profile?.semantic_columns || [];
  const columnProfiles = profile?.column_profiles || [];
  const [editingCol, setEditingCol] = useState<string | null>(null);
  const [selectedRole, setSelectedRole] = useState<SemanticRole>("DIMENSION");
  const [isSaving, setIsSaving] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");
  const [filterRole, setFilterRole] = useState<string>("ALL");

  const colProfilesMap = useMemo(
    () => new Map(columnProfiles.map((c) => [c.column_name, c])),
    [columnProfiles]
  );

  if (!profile || semanticCols.length === 0) {
    return (
      <div className="p-8 text-center text-slate bg-surface rounded-2xl border border-border shadow-soft">
        No semantic metadata available. Run the profiler to discover semantic roles.
      </div>
    );
  }

  const handleSaveOverride = async (colName: string) => {
    setIsSaving(true);
    try {
      await api.patch(
        `/api/v1/datasets/${datasetId}/versions/${versionId}/semantics/${encodeURIComponent(colName)}`,
        { user_role: selectedRole }
      );
      setEditingCol(null);
      onRefresh();
    } catch (error) {
      console.error("Failed to update semantic override:", error);
    } finally {
      setIsSaving(false);
    }
  };

  const getRoleIcon = (role: string, isCurrency?: boolean) => {
    if (role === "MEASURE" && isCurrency) {
      return <CircleDollarSign className="h-4 w-4 text-emerald-600" />;
    }
    if (role === "MEASURE") {
      return <Hash className="h-4 w-4 text-teal" />;
    }
    if (role === "DIMENSION") {
      return <Layers className="h-4 w-4 text-blue" />;
    }
    if (role === "IDENTIFIER") {
      return <KeyRound className="h-4 w-4 text-amber" />;
    }
    if (role === "DATE" || role === "DATETIME") {
      return <Calendar className="h-4 w-4 text-purple-600" />;
    }
    return <HelpCircle className="h-4 w-4 text-slate" />;
  };

  const getRoleTheme = (role: string, isCurrency?: boolean) => {
    if (role === "MEASURE" && isCurrency) {
      return "bg-emerald-50 text-emerald-700 border-emerald-200";
    }
    if (role === "MEASURE") {
      return "bg-teal-soft text-teal border-teal-border";
    }
    if (role === "DIMENSION") {
      return "bg-blue-soft text-blue border-blue-border";
    }
    if (role === "IDENTIFIER") {
      return "bg-amber-soft text-amber border-amber-border";
    }
    if (role === "DATE" || role === "DATETIME") {
      return "bg-purple-50 text-purple-700 border-purple-200";
    }
    return "bg-cloud text-slate border-border";
  };

  const filteredColumns = semanticCols.filter((s) => {
    const matchesSearch = s.column_name.toLowerCase().includes(searchQuery.toLowerCase());
    const activeRole = s.user_role || s.inferred_role;
    if (filterRole === "ALL") return matchesSearch;
    if (filterRole === "MEASURE") return matchesSearch && activeRole === "MEASURE";
    if (filterRole === "DIMENSION") return matchesSearch && activeRole === "DIMENSION";
    if (filterRole === "IDENTIFIER") return matchesSearch && activeRole === "IDENTIFIER";
    if (filterRole === "TEMPORAL") return matchesSearch && ["DATE", "DATETIME"].includes(activeRole);
    return matchesSearch;
  });

  const measures = semanticCols.filter((s) => (s.user_role || s.inferred_role) === "MEASURE");
  const dimensions = semanticCols.filter((s) => (s.user_role || s.inferred_role) === "DIMENSION");
  const identifiers = semanticCols.filter((s) => (s.user_role || s.inferred_role) === "IDENTIFIER");
  const temporals = semanticCols.filter((s) => ["DATE", "DATETIME"].includes(s.user_role || s.inferred_role));

  const renderColumnCard = (s: SemanticColumn) => {
    const isEditing = editingCol === s.column_name;
    const activeRole = s.user_role || s.inferred_role;
    const confidencePct = Math.round(s.inferred_confidence * 100);
    const colProfile = colProfilesMap.get(s.column_name);

    return (
      <Card
        key={s.id}
        className={cn(
          "rounded-2xl border border-border bg-surface p-4 sm:p-5 shadow-soft hover:shadow-soft-md hover:border-teal/30 transition-all flex flex-col justify-between h-full group relative",
          isEditing && "ring-2 ring-teal ring-offset-1 border-teal"
        )}
      >
        {/* Top & Middle Section */}
        <div className="space-y-3.5">
          {/* Header Row: Column Name & Role Badges */}
          <div className="flex items-start justify-between gap-3">
            <div className="flex items-center gap-2.5 min-w-0 flex-1">
              <div
                className={cn(
                  "flex h-9 w-9 items-center justify-center rounded-xl border shrink-0 transition-colors",
                  getRoleTheme(activeRole, s.possible_currency)
                )}
              >
                {getRoleIcon(activeRole, s.possible_currency)}
              </div>
              <div className="min-w-0 flex-1">
                <span
                  className="font-mono text-xs sm:text-sm font-bold text-ink group-hover:text-teal transition-colors truncate block"
                  title={s.column_name}
                >
                  {s.column_name}
                </span>
                <span className="text-[11px] text-slate font-medium truncate block">
                  {colProfile?.data_type || activeRole.toLowerCase()}
                </span>
              </div>
            </div>

            {/* Badges */}
            <div className="flex items-center gap-1.5 flex-wrap justify-end shrink-0">
              {s.user_role ? (
                <Badge variant="teal" dot className="text-[10px] font-semibold py-0.5 px-2">
                  User: {s.user_role}
                </Badge>
              ) : (
                <span
                  className={cn(
                    "inline-flex items-center rounded-full px-2 py-0.5 text-[10px] font-semibold border uppercase tracking-wider",
                    getRoleTheme(activeRole, false)
                  )}
                >
                  {s.inferred_role}
                </span>
              )}
              {s.possible_currency && (
                <span className="inline-flex items-center rounded-full px-2 py-0.5 text-[10px] font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200">
                  Currency
                </span>
              )}
            </div>
          </div>

          {/* Contextual Stats Pill (Human-Crafted Data Summary) */}
          <div className="rounded-xl bg-cloud/50 p-2.5 border border-border/70 text-xs">
            <div className="grid grid-cols-2 gap-2 text-[11px]">
              <div>
                <span className="text-slate/80 block text-[10px] font-medium uppercase tracking-wider">
                  Data Type
                </span>
                <span className="font-mono font-semibold text-ink truncate block">
                  {colProfile?.data_type || "Inferred"}
                </span>
              </div>
              <div>
                <span className="text-slate/80 block text-[10px] font-medium uppercase tracking-wider">
                  Distinct Values
                </span>
                <span className="font-mono font-semibold text-ink truncate block">
                  {colProfile?.unique_count !== undefined
                    ? `${colProfile.unique_count.toLocaleString()} (${colProfile.unique_percentage.toFixed(0)}%)`
                    : "100% Unique"}
                </span>
              </div>
            </div>
          </div>
        </div>

        {/* Footer Section: Confidence Gauge + Edit Action */}
        <div className="mt-4 pt-3 border-t border-border/80 flex items-center justify-between gap-2">
          {/* Confidence Meter */}
          {!s.user_role ? (
            <div className="flex items-center gap-2 min-w-0" title={`Inference confidence: ${confidencePct}%`}>
              <span className="text-[10px] text-slate font-medium uppercase tracking-wider shrink-0">
                Confidence
              </span>
              <div className="w-16 sm:w-20 bg-cloud rounded-full h-1.5 overflow-hidden shrink-0 border border-border/40">
                <div
                  className={cn(
                    "h-full rounded-full transition-all",
                    confidencePct >= 85 ? "bg-teal" : confidencePct >= 65 ? "bg-amber" : "bg-slate"
                  )}
                  style={{ width: `${confidencePct}%` }}
                />
              </div>
              <span className="font-mono text-[11px] font-semibold text-ink shrink-0">
                {confidencePct}%
              </span>
            </div>
          ) : (
            <div className="flex items-center gap-1.5 text-[11px] text-teal font-medium">
              <CheckCircle2 className="h-3.5 w-3.5 text-teal" />
              <span>User Overridden</span>
            </div>
          )}

          {/* Edit Button */}
          {!isEditing && (
            <button
              onClick={() => {
                setEditingCol(s.column_name);
                setSelectedRole(activeRole);
              }}
              className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-xs font-semibold text-slate hover:text-teal hover:bg-teal-soft/60 transition-colors shrink-0"
              title="Change semantic role"
            >
              <Pencil className="h-3 w-3" />
              <span>Edit</span>
            </button>
          )}
        </div>

        {/* Inline Override Panel */}
        {isEditing && (
          <div className="mt-3 pt-3 border-t border-border space-y-2.5 bg-cloud/40 -mx-4 -mb-4 sm:-mx-5 sm:-mb-5 p-3.5 sm:p-4 rounded-b-2xl">
            <div className="flex items-center justify-between">
              <label className="text-[10px] font-semibold uppercase tracking-wider text-slate block">
                Override Role
              </label>
              <span className="text-[10px] text-slate">Assign manual classification</span>
            </div>
            <Select
              options={ROLE_OPTIONS}
              value={selectedRole}
              onChange={(e) => setSelectedRole(e.target.value as SemanticRole)}
              className="text-xs h-8"
            />
            <div className="flex items-center justify-end gap-2 pt-1">
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setEditingCol(null)}
                disabled={isSaving}
                className="h-7 text-xs px-2.5"
              >
                Cancel
              </Button>
              <Button
                variant="primary"
                size="sm"
                onClick={() => handleSaveOverride(s.column_name)}
                isLoading={isSaving}
                className="h-7 text-xs px-3"
              >
                Save
              </Button>
            </div>
          </div>
        )}
      </Card>
    );
  };

  return (
    <div className="space-y-6">
      {/* Top Banner & Search Filter Bar */}
      <div className="p-4 sm:p-5 rounded-2xl bg-surface border border-border shadow-soft flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-teal-soft text-teal">
              <Sparkles className="h-3.5 w-3.5" />
            </div>
            <h3 className="text-sm font-bold text-ink">Semantic Classification Layer</h3>
          </div>
          <p className="text-xs text-slate mt-1 max-w-xl leading-relaxed">
            Deterministic inference categorizes attributes into analytical roles. Roles dictate how the AI Analyst, Visualizer, and SQL Engine aggregate or group your data.
          </p>
        </div>

        {/* Search & Filter Controls */}
        <div className="flex items-center gap-2.5 flex-wrap sm:flex-nowrap">
          <div className="relative w-full sm:w-56">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-slate/70" />
            <input
              type="text"
              placeholder="Search fields..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-9 pr-3 py-1.5 rounded-xl border border-border bg-cloud text-xs text-ink placeholder:text-slate focus:border-teal focus:outline-none focus:ring-1 focus:ring-teal"
            />
          </div>
        </div>
      </div>

      {/* Role Filter Tabs */}
      <div className="flex items-center gap-1.5 overflow-x-auto pb-1 no-scrollbar">
        {[
          { key: "ALL", label: `All Fields (${semanticCols.length})` },
          { key: "MEASURE", label: `Measures (${measures.length})` },
          { key: "DIMENSION", label: `Dimensions (${dimensions.length})` },
          { key: "IDENTIFIER", label: `Identifiers (${identifiers.length})` },
          { key: "TEMPORAL", label: `Temporal (${temporals.length})` },
        ].map((tab) => (
          <button
            key={tab.key}
            onClick={() => setFilterRole(tab.key)}
            className={cn(
              "px-3 py-1.5 rounded-xl text-xs font-semibold whitespace-nowrap transition-all",
              filterRole === tab.key
                ? "bg-teal text-white shadow-soft"
                : "bg-surface border border-border text-slate hover:text-ink hover:bg-cloud"
            )}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Column Cards Grid */}
      {filteredColumns.length === 0 ? (
        <div className="p-8 text-center rounded-2xl border border-dashed border-border bg-cloud/30 text-xs text-slate">
          No fields found matching &quot;{searchQuery}&quot; in this category.
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 items-stretch">
          {filteredColumns.map(renderColumnCard)}
        </div>
      )}
    </div>
  );
}
