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
      <div className="p-8 text-center text-slate-400 bg-slate-900/30 rounded-xl border border-slate-800">
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
          className="max-w-md bg-slate-900/50 border-slate-800"
        />
        <div className="text-xs text-slate-400">
          Showing {filteredColumns.length} of {profile.column_profiles.length} columns
        </div>
      </div>

      <div className="rounded-xl border border-slate-800 bg-slate-900/40 overflow-hidden">
        <Table>
          <TableHeader>
            <TableRow className="border-slate-800 hover:bg-transparent">
              <TableHead className="w-12 text-slate-400">#</TableHead>
              <TableHead className="text-slate-300">Column Name</TableHead>
              <TableHead className="text-slate-300">Conceptual Type</TableHead>
              <TableHead className="text-slate-300">Native Type</TableHead>
              <TableHead className="text-slate-300">Inferred Role</TableHead>
              <TableHead className="text-slate-300">Confidence</TableHead>
              <TableHead className="text-slate-300">Nulls</TableHead>
              <TableHead className="text-slate-300">Uniques</TableHead>
              <TableHead className="text-slate-300">Flags</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {filteredColumns.map((col) => {
              const sem = semanticMap.get(col.column_name);
              const role = sem?.user_role || sem?.inferred_role || "UNKNOWN";
              const confidence = sem ? Math.round(sem.inferred_confidence * 100) : 0;

              return (
                <TableRow key={col.id} className="border-slate-800 hover:bg-slate-800/40">
                  <TableCell className="font-mono text-xs text-slate-500">
                    {col.ordinal_position + 1}
                  </TableCell>
                  <TableCell className="font-medium text-slate-200">
                    <div>{col.column_name}</div>
                    {col.normalized_name !== col.column_name.toLowerCase() && (
                      <div className="text-xs font-mono text-slate-500">
                        {col.normalized_name}
                      </div>
                    )}
                  </TableCell>
                  <TableCell>
                    <Badge variant={getTypeBadgeVariant(col.conceptual_type)}>
                      {col.conceptual_type}
                    </Badge>
                  </TableCell>
                  <TableCell className="font-mono text-xs text-slate-400">
                    {col.data_type}
                  </TableCell>
                  <TableCell>
                    <Badge variant={getRoleBadgeVariant(role)}>
                      {role}
                    </Badge>
                  </TableCell>
                  <TableCell>
                    <div className="flex items-center gap-2">
                      <div className="w-16 bg-slate-800 rounded-full h-1.5 overflow-hidden">
                        <div
                          className="bg-indigo-500 h-1.5 rounded-full"
                          style={{ width: `${confidence}%` }}
                        />
                      </div>
                      <span className="text-xs text-slate-400">{confidence}%</span>
                    </div>
                  </TableCell>
                  <TableCell>
                    <span
                      className={`text-xs ${
                        col.null_percentage > 20
                          ? "text-red-400 font-semibold"
                          : col.null_percentage > 0
                          ? "text-amber-400"
                          : "text-slate-400"
                      }`}
                    >
                      {col.null_count} ({col.null_percentage}%)
                    </span>
                  </TableCell>
                  <TableCell className="text-xs text-slate-400">
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
