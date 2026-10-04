# Phase 8 — Frontend Dashboard Editor & User Control

## 1. Dashboard Workspace Features

The frontend dashboard workspace provides intuitive, high-agency controls:
- **Header**: Dataset and version visibility (`Dataset: Sales (v2)`), generation status badge, last-updated timestamp.
- **Top Actions**: Quality Score inspection, Data Refresh, Layout Edit Mode toggle, Dashboard Deletion.
- **AI Refinement Bar**: Natural-language prompt box allowing conversational adjustments ("Change chart to donut", "Remove customer table").
- **Filter Bar**: Dynamic pill selectors for categorical, date, and numeric filters.
- **12-Column Responsive Card Grid**: High-contrast, clean Soft UI cards with interactive charts.
- **Provenance Inspector**: Modal displaying exact DuckDB analysis query parameters, execution status, and raw table sample.

## 2. Edit Mode Operations

When "Edit Layout" is toggled:
- **Span Resizing**: Dropdown allows instant adjustment between Span 3 (1/4), Span 4 (1/3), Span 6 (1/2), Span 8 (2/3), Span 12 (Full).
- **Chart Switching**: Dropdown allows changing chart type across supported visualizations (bar, horizontal bar, line, area, pie, donut, scatter, histogram, boxplot, table).
- **Removal**: Single-click delete with automatic grid reflow.
- **Save**: Atomic patch updates sent to `/api/v1/dashboards/{id}/patches` with rollback protection.
