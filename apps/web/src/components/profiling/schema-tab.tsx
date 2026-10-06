"use client";

import React, { useState } from "react";
import { DatasetProfile } from "@/types";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";

interface SchemaTabProps {
  profile: DatasetProfile | null;
}

export function SchemaTab({ profile }: SchemaTabProps) {
  const [search, setSearch] = useState("");

  if (!profile || !profile.column_profiles || profile.column_profiles.length === 0) {
    return (
      <div className="p-8 text-center text-slate bg-surface rounded-xl border border-border shadow-soft">
        No schema available. Run the profiler to inspect columns.
      </div>
    );
  }

  // Create lookup for semantic role and confidence by column_name
  const semanticMap = new Map(
    profile.semantic_columns?.map((s) => [s.column_name, s]) || []
  );

  const filteredColumns = profile.column_profiles.filter((col) =>
    col.column_name.toLowerCase().includes(search.toLowerCase()) ||
    col.data_type.toLowerCase().includes(search.toLowerCase()) ||
    col.conceptual_type.toLowerCase().includes(search.toLowerCase())
  );

  const getTypeBadgeVariant = (type: string): "blue" | "outline" | "amber" | "teal" => {
    switch (type) {
      case "INTEGER":
      case "FLOAT":
        return "blue";
      case "STRING":
        return "outline";
      case "BOOLEAN":
        return "amber";
      case "DATE":
      case "DATETIME":
        return "teal";
      default:
        return "outline";
    }
  };

  const getRoleBadgeVariant = (role: string): "blue" | "teal" | "amber" | "outline" => {
    switch (role) {
      case "MEASURE":
        return "blue";
      case "DIMENSION":
        return "teal";
      case "IDENTIFIER":
        return "amber";
      case "DATE":
      case "DATETIME":
        return "outline";
      default:
        return "outline";
    }
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between gap-4">
        <Input
          placeholder="Filter columns by name or type..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="max-w-md bg-surface border-border"
        />
        <div className="text-xs text-slate">
          Showing {filteredColumns.length} of {profile.column_profiles.length} columns
        </div>
      </div>

      <div className="rounded-xl border border-border bg-surface shadow-soft overflow-hidden">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead className="w-12">#</TableHead>
              <TableHead>Column Name</TableHead>
              <TableHead>Conceptual Type</TableHead>
              <TableHead>Native Type</TableHead>
              <TableHead>Inferred Role</TableHead>
              <TableHead>Confidence</TableHead>
              <TableHead>Nulls</TableHead>
              <TableHead>Uniques</TableHead>
              <TableHead>Flags</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {filteredColumns.map((col) => {
              const sem = semanticMap.get(col.column_name);
              const role = sem?.user_role || sem?.inferred_role || "UNKNOWN";
              const confidence = sem ? Math.round(sem.inferred_confidence * 100) : 0;

              return (
                <TableRow key={col.id}>
                  <TableCell className="font-mono text-xs text-slate">
                    {col.ordinal_position + 1}
                  </TableCell>
                  <TableCell className="font-medium text-ink">
                    <div>{col.column_name}</div>
                    {col.normalized_name !== col.column_name.toLowerCase() && (
                      <div className="text-xs font-mono text-slate">
                        {col.normalized_name}
                      </div>
                    )}
                  </TableCell>
                  <TableCell>
                    <Badge variant={getTypeBadgeVariant(col.conceptual_type)}>
                      {col.conceptual_type}
                    </Badge>
                  </TableCell>
                  <TableCell className="font-mono text-xs text-slate">
                    {col.data_type}
                  </TableCell>
                  <TableCell>
                    <Badge variant={getRoleBadgeVariant(role)}>
                      {role}
                    </Badge>
                  </TableCell>
                  <TableCell>
                    <div className="flex items-center gap-2">
                      <div className="w-16 bg-cloud-subtle rounded-full h-1.5 overflow-hidden border border-border-subtle">
                        <div
                          className="bg-teal h-1.5 rounded-full"
                          style={{ width: `${confidence}%` }}
                        />
                      </div>
                      <span className="text-xs text-slate font-mono">{confidence}%</span>
                    </div>
                  </TableCell>
                  <TableCell>
                    <span
                      className={`text-xs ${
                        col.null_percentage > 20
                          ? "text-rose font-semibold"
                          : col.null_percentage > 0
                          ? "text-amber font-medium"
                          : "text-slate"
                      }`}
                    >
                      {col.null_count} ({col.null_percentage}%)
                    </span>
                  </TableCell>
                  <TableCell className="text-xs text-slate">
                    {col.unique_count} ({col.unique_percentage}%)
                  </TableCell>
                  <TableCell>
                    <div className="flex gap-1 flex-wrap">
                      {col.is_constant && (
                        <Badge variant="amber">
                          Constant
                        </Badge>
                      )}
                      {col.is_near_constant && (
                        <Badge variant="outline">
                          Near Constant
                        </Badge>
                      )}
                      {col.outlier_count > 0 && (
                        <Badge variant="outline">
                          {col.outlier_count} Outliers
                        </Badge>
                      )}
                      {sem?.possible_currency && (
                        <Badge variant="teal">
                          Currency
                        </Badge>
                      )}
                    </div>
                  </TableCell>
                </TableRow>
              );
            })}
          </TableBody>
        </Table>
      </div>
    </div>
  );
}
