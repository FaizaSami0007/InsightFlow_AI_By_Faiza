"use client";

import React, { useState } from "react";
import { DatasetProfile, SemanticColumn, SemanticRole } from "@/types";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Select } from "@/components/ui/select";
import { Button } from "@/components/ui/button";
import { api } from "@/lib/api-client";

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
  const [editingCol, setEditingCol] = useState<string | null>(null);
  const [selectedRole, setSelectedRole] = useState<SemanticRole>("DIMENSION");
  const [isSaving, setIsSaving] = useState(false);

  if (!profile || semanticCols.length === 0) {
    return (
      <div className="p-8 text-center text-slate-400 bg-slate-900/30 rounded-xl border border-slate-800">
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

  const measures = semanticCols.filter((s) => (s.user_role || s.inferred_role) === "MEASURE");
  const dimensions = semanticCols.filter((s) => (s.user_role || s.inferred_role) === "DIMENSION");
  const identifiers = semanticCols.filter((s) => (s.user_role || s.inferred_role) === "IDENTIFIER");
  const temporals = semanticCols.filter((s) => ["DATE", "DATETIME"].includes(s.user_role || s.inferred_role));

  const renderColumnCard = (s: SemanticColumn) => {
    const isEditing = editingCol === s.column_name;
    const activeRole = s.user_role || s.inferred_role;
    const confidencePct = Math.round(s.inferred_confidence * 100);

    return (
      <Card key={s.id} className="p-4 bg-slate-950/60 border-slate-800 space-y-3">
        <div className="flex items-start justify-between gap-2">
          <div>
            <div className="text-sm font-semibold text-slate-200">{s.column_name}</div>
            <p className="text-xs text-slate-400 mt-0.5">{s.description}</p>
          </div>
          <div className="flex flex-col items-end gap-1">
            <Badge variant={s.user_role ? "blue" : "outline"}>
              {s.user_role ? `User: ${s.user_role}` : `Inferred: ${s.inferred_role}`}
            </Badge>
            {s.possible_currency && (
              <Badge variant="teal">
                Currency
              </Badge>
            )}
          </div>
        </div>

        {/* Confidence bar */}
        {!s.user_role && (
          <div className="space-y-1">
            <div className="flex justify-between text-xs text-slate-500">
              <span>Confidence</span>
              <span>{confidencePct}%</span>
            </div>
            <div className="w-full bg-slate-800 rounded-full h-1.5 overflow-hidden">
              <div
                className="bg-indigo-500 h-1.5 rounded-full"
                style={{ width: `${confidencePct}%` }}
              />
            </div>
          </div>
        )}

        {/* User Override action */}
        {isEditing ? (
          <div className="pt-2 border-t border-slate-800 space-y-2">
            <label className="text-xs font-medium text-slate-400">Override Semantic Role</label>
            <Select
              options={ROLE_OPTIONS}
              value={selectedRole}
              onChange={(e) => setSelectedRole(e.target.value as SemanticRole)}
              className="text-xs"
            />
            <div className="flex gap-2 justify-end pt-1">
              <Button
                variant="outline"
                size="sm"
                onClick={() => setEditingCol(null)}
                disabled={isSaving}
              >
                Cancel
              </Button>
              <Button
                variant="primary"
                size="sm"
                onClick={() => handleSaveOverride(s.column_name)}
                isLoading={isSaving}
              >
                Save
              </Button>
            </div>
          </div>
        ) : (
          <div className="flex justify-end pt-1">
            <button
              onClick={() => {
                setEditingCol(s.column_name);
                setSelectedRole(activeRole);
              }}
              className="text-xs text-indigo-400 hover:text-indigo-300 font-medium"
            >
              Override Role &rarr;
            </button>
          </div>
        )}
      </Card>
    );
  };

  return (
    <div className="space-y-6">
      <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 flex items-center justify-between">
        <div>
          <h3 className="text-sm font-semibold text-slate-200">Semantic Classification Layer</h3>
          <p className="text-xs text-slate-400 mt-0.5">
            Deterministic inference categorizes fields into analytical roles. You can manually override any classification.
          </p>
        </div>
      </div>

      {/* Measures Section */}
      <div className="space-y-3">
        <div className="flex items-center gap-2">
          <Badge variant="blue">
            Measures ({measures.length})
          </Badge>
          <span className="text-xs text-slate-400">Quantitative numeric variables suitable for aggregation</span>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {measures.map(renderColumnCard)}
        </div>
      </div>

      {/* Dimensions Section */}
      <div className="space-y-3">
        <div className="flex items-center gap-2">
          <Badge variant="teal">
            Dimensions ({dimensions.length})
          </Badge>
          <span className="text-xs text-slate-400">Qualitative categorical attributes suitable for grouping and filtering</span>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {dimensions.map(renderColumnCard)}
        </div>
      </div>

      {/* Identifiers & Temporal Section */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="space-y-3">
          <div className="flex items-center gap-2">
            <Badge variant="amber">
              Identifiers ({identifiers.length})
            </Badge>
            <span className="text-xs text-slate-400">Keys and IDs</span>
          </div>
          <div className="space-y-3">{identifiers.map(renderColumnCard)}</div>
        </div>

        <div className="space-y-3">
          <div className="flex items-center gap-2">
            <Badge variant="outline">
              Temporal ({temporals.length})
            </Badge>
            <span className="text-xs text-slate-400">Dates and Timestamps</span>
          </div>
          <div className="space-y-3">{temporals.map(renderColumnCard)}</div>
        </div>
      </div>
    </div>
  );
}
