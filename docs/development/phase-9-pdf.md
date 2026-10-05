# Phase 9: PDF Export Architecture & Engine

## 1. Overview

The PDF export subsystem translates a validated InsightFlow dashboard into structured, multi-page vector PDF documents. It is implemented using ReportLab's Platypus flowable framework.

---

## 2. Layout Structure

Each generated PDF document contains:
1. **Document Header Banner:**
   - Report Title (defaulting to dashboard name, with user override support)
   - Dataset Identifier & Version Number
   - Generation Timestamp (UTC & localized)
   - Active Filter Snapshot (e.g., `Region = North`, `Year = 2026`)
2. **KPI Highlights Grid:**
   - Rendered as soft-bordered card callouts with bold metrics, labels, and formatted values.
3. **Chart & Table Widget Flowables:**
   - Analytical Charts: Rendered as high-resolution embedded visual diagrams or structured categorical summary tables.
   - Tabular Result Sets: Styled tables with alternate row shading, bold headers, and column wrapping.
4. **Analytical Provenance & Audit Trail Footer:**
   - Dataset version checksum, tool operations executed, execution duration in milliseconds, and InsightFlow provenance stamps.

---

## 3. Page Configuration & Options

- **Page Sizes:**
  - `A4`: 210 × 297 mm (Standard ISO 216)
  - `Letter`: 8.5 × 11 in (ANSI A)
- **Orientations:**
  - `landscape` (Default for dashboard-heavy reporting)
  - `portrait` (For document-centric summaries)
- **Margins & Page Breaks:**
  - Standard 0.5-inch margins (36 pt)
  - Widgets enforce flowable page-break safety to prevent card slicing across page boundaries.
