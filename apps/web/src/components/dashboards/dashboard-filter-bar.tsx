"use client";

import React from "react";
import { DashboardFilter } from "@/types";
import { Filter, Calendar, Tag, Hash, X } from "lucide-react";

interface DashboardFilterBarProps {
  filters: DashboardFilter[];
  activeFilters: Record<string, unknown>;
  onFilterChange: (columnName: string, value: unknown) => void;
  onClearFilter: (columnName: string) => void;
  disabled?: boolean;
}

export function DashboardFilterBar({
  filters,
  activeFilters,
  onFilterChange,
  onClearFilter,
  disabled = false,
}: DashboardFilterBarProps) {
  if (!filters || filters.length === 0) {
    return null;
  }

  return (
    <div className="flex flex-wrap items-center gap-3 bg-white border border-[#E3E8EF] px-4 py-2.5 rounded-lg shadow-sm">
      <div className="flex items-center gap-1.5 text-xs font-semibold text-[#536176] uppercase tracking-wider mr-1">
        <Filter className="w-3.5 h-3.5 text-[#0F766E]" />
        <span>Filters</span>
      </div>

      {filters.map((f) => {
        const activeVal = activeFilters[f.column_name];
        const isSet = activeVal !== undefined && activeVal !== null && activeVal !== "";

        return (
          <div
            key={f.id || f.column_name}
            className={`flex items-center gap-2 px-3 py-1.5 rounded-md text-xs transition-colors border ${
              isSet
                ? "bg-[#E6F4F1] border-[#0F766E] text-[#0F766E]"
                : "bg-[#F7F9FC] border-[#E3E8EF] text-[#172033]"
            }`}
          >
            {f.filter_type === "temporal" && <Calendar className="w-3.5 h-3.5 opacity-70" />}
            {f.filter_type === "categorical" && <Tag className="w-3.5 h-3.5 opacity-70" />}
            {f.filter_type === "numeric" && <Hash className="w-3.5 h-3.5 opacity-70" />}

            <span className="font-medium">{f.display_name}:</span>

            {f.allowed_values && f.allowed_values.length > 0 ? (
              <select
                value={isSet ? String(activeVal) : ""}
                onChange={(e) => onFilterChange(f.column_name, e.target.value || null)}
                disabled={disabled}
                className="bg-transparent font-semibold border-none focus:outline-none cursor-pointer pr-1 text-xs"
              >
                <option value="">All</option>
                {f.allowed_values.map((val) => (
                  <option key={String(val)} value={String(val)}>
                    {String(val)}
                  </option>
                ))}
              </select>
            ) : (
              <input
                type="text"
                placeholder="Any"
                value={isSet ? String(activeVal) : ""}
                onChange={(e) => onFilterChange(f.column_name, e.target.value || null)}
                disabled={disabled}
                className="bg-transparent border-b border-dashed border-current px-1 py-0.5 w-24 focus:outline-none text-xs font-semibold"
              />
            )}

            {isSet && (
              <button
                type="button"
                onClick={() => onClearFilter(f.column_name)}
                disabled={disabled}
                className="ml-1 hover:bg-black/10 rounded p-0.5 text-current focus:outline-none"
                title="Clear filter"
              >
                <X className="w-3 h-3" />
              </button>
            )}
          </div>
        );
      })}
    </div>
  );
}
