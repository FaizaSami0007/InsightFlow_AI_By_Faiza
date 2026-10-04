"use client";

import React, { useState } from "react";
import { Download, ChevronLeft, ChevronRight, ArrowUpDown } from "lucide-react";

interface DataTableProps {
  columns: string[];
  data: Record<string, unknown>[];
  title?: string;
  pageSize?: number;
}

export function DataTable({ columns, data, title, pageSize = 10 }: DataTableProps) {
  const [currentPage, setCurrentPage] = useState(1);
  const [sortCol, setSortCol] = useState<string | null>(null);
  const [sortAsc, setSortAsc] = useState(true);

  if (!data || data.length === 0) {
    return (
      <div className="p-8 text-center text-sm text-slate border border-border rounded-xl bg-cloud/50">
        No records available to display in table.
      </div>
    );
  }

  const tableCols = columns && columns.length > 0 ? columns : Object.keys(data[0] || {});

  // Sorting
  const sortedData = [...data].sort((a, b) => {
    if (!sortCol) return 0;
    const valA = a[sortCol];
    const valB = b[sortCol];
    if (valA === valB) return 0;
    if (valA === null || valA === undefined) return 1;
    if (valB === null || valB === undefined) return -1;
    if (typeof valA === "number" && typeof valB === "number") {
      return sortAsc ? valA - valB : valB - valA;
    }
    return sortAsc
      ? String(valA).localeCompare(String(valB))
      : String(valB).localeCompare(String(valA));
  });

  const totalPages = Math.ceil(sortedData.length / pageSize);
  const startIndex = (currentPage - 1) * pageSize;
  const pageData = sortedData.slice(startIndex, startIndex + pageSize);

  const handleSort = (col: string) => {
    if (sortCol === col) {
      setSortAsc(!sortAsc);
    } else {
      setSortCol(col);
      setSortAsc(true);
    }
  };

  const exportCSV = () => {
    const headers = tableCols.join(",");
    const rows = sortedData.map((row) =>
      tableCols
        .map((col) => {
          const val = row[col];
          if (typeof val === "string" && val.includes(",")) {
            return `"${val}"`;
          }
          return val !== null && val !== undefined ? String(val) : "";
        })
        .join(",")
    );
    const csvContent = "data:text/csv;charset=utf-8," + [headers, ...rows].join("\n");
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement("a");
    link.setAttribute("href", encodedUri);
    link.setAttribute("download", `${title || "analysis_data"}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  return (
    <div className="flex flex-col border border-border rounded-xl bg-surface overflow-hidden shadow-sm">
      <div className="flex items-center justify-between px-4 py-3 border-b border-border bg-cloud/40">
        <span className="text-xs font-semibold text-slate uppercase tracking-wider">
          {sortedData.length} Records
        </span>
        <button
          onClick={exportCSV}
          className="flex items-center gap-1.5 text-xs font-medium text-slate hover:text-ink px-2.5 py-1 rounded-md border border-border hover:bg-surface transition-colors"
          title="Export CSV"
        >
          <Download className="w-3.5 h-3.5 text-slate" />
          <span>Export CSV</span>
        </button>
      </div>

      <div className="overflow-x-auto max-w-full">
        <table className="w-full text-left text-xs border-collapse">
          <thead>
            <tr className="border-b border-border bg-cloud/60">
              <th className="py-2.5 px-3 font-semibold text-slate w-12 text-center">#</th>
              {tableCols.map((col) => (
                <th
                  key={col}
                  onClick={() => handleSort(col)}
                  className="py-2.5 px-4 font-semibold text-ink cursor-pointer hover:bg-border/40 select-none transition-colors"
                >
                  <div className="flex items-center gap-1.5">
                    <span>{col.replace(/_/g, " ").toUpperCase()}</span>
                    <ArrowUpDown className="w-3 h-3 text-slate/70" />
                  </div>
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-border/60">
            {pageData.map((row, idx) => (
              <tr key={idx} className="hover:bg-cloud/30 transition-colors">
                <td className="py-2.5 px-3 text-center text-slate font-mono text-[11px]">
                  {startIndex + idx + 1}
                </td>
                {tableCols.map((col) => {
                  const val = row[col];
                  const isNum = typeof val === "number";
                  return (
                    <td
                      key={col}
                      className={`py-2.5 px-4 text-ink font-mono text-xs ${
                        isNum ? "text-right font-medium text-teal" : ""
                      }`}
                    >
                      {val !== null && val !== undefined
                        ? isNum
                          ? val.toLocaleString(undefined, { maximumFractionDigits: 2 })
                          : String(val)
                        : "—"}
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {totalPages > 1 && (
        <div className="flex items-center justify-between px-4 py-2.5 border-t border-border bg-cloud/20 text-xs text-slate">
          <span>
            Page {currentPage} of {totalPages}
          </span>
          <div className="flex items-center gap-1">
            <button
              onClick={() => setCurrentPage((p) => Math.max(p - 1, 1))}
              disabled={currentPage === 1}
              className="p-1 rounded hover:bg-surface border border-border disabled:opacity-40 disabled:cursor-not-allowed"
            >
              <ChevronLeft className="w-4 h-4" />
            </button>
            <button
              onClick={() => setCurrentPage((p) => Math.min(p + 1, totalPages))}
              disabled={currentPage === totalPages}
              className="p-1 rounded hover:bg-surface border border-border disabled:opacity-40 disabled:cursor-not-allowed"
            >
              <ChevronRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
