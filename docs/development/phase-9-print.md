# Phase 9: Print-Friendly Media Engine

## 1. Overview

The print engine provides instant, zero-latency physical paper printing and native browser PDF output directly from the client interface.

---

## 2. Print Stylesheet Implementation (`apps/web/src/app/globals.css`)

The system implements `@media print` rules:

```css
@media print {
  @page {
    margin: 1.5cm;
    size: auto;
  }

  body {
    background-color: #ffffff !important;
    color: #0f172a !important;
    -webkit-print-color-adjust: exact !important;
    print-color-adjust: exact !important;
  }

  /* Hide interactive controls, sidebars, headers, dialogs and toasts */
  nav,
  aside,
  button,
  form,
  input,
  select,
  [role="dialog"],
  [role="status"],
  .no-print {
    display: none !important;
  }

  /* Page break rules */
  article,
  section,
  .dashboard-widget-card,
  [data-widget-card] {
    break-inside: avoid !important;
    page-break-inside: avoid !important;
    box-shadow: none !important;
    border: 1px solid #e2e8f0 !important;
    margin-bottom: 1rem !important;
  }
}
```

---

## 3. Preserved Print Elements

- Complete Dashboard Title & Description
- Active Filter State Callout
- Dataset & Version Metadata Lineage
- All KPI Callouts, Visual Charts, and Tabular Widgets
- Analytical Provenance Stamps
