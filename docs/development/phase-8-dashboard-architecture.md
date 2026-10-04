# Phase 8 — Context-Aware Dashboard Architecture

## 1. Overview & Core Philosophy

InsightFlow AI Phase 8 introduces context-aware dashboard generation and lifecycle management. The core architectural tenet is:
**The AI MUST NOT generate executable code, HTML, CSS, JavaScript, React components, or arbitrary SQL strings.**

Instead, the dashboard intelligence pipeline operates through structured declarative specifications:

```
USER INTENT / PURPOSE
        │
        ▼
AI DASHBOARD PLANNER (Grounding in Dataset Semantic Profile)
        │
        ▼
STRUCTURED DASHBOARD PLAN (Pydantic / JSON schema)
        │
        ▼
DETERMINISTIC PLAN VALIDATOR (Bounds, Column Exists, Semantic Roles)
        │
    ┌───┴───────────────────────────────┐
    ▼                                   ▼
ANALYTICAL TOOL ENGINE (DuckDB)   VISUALIZATION RECOMMENDATION ENGINE
    │                                   │
    └───────────────────┬───────────────┘
                        ▼
            VALIDATED ATOMIC WIDGETS
                        │
                        ▼
      12-COLUMN DETERMINISTIC LAYOUT ENGINE (Auto-placement & reflow)
                        │
                        ▼
              DASHBOARD SPECIFICATION (Persistent Database Model)
                        │
                        ▼
      DETERMINISTIC FRONTEND RENDERER (Clean Soft UI Cards)
                        │
                        ▼
            USER REFINEMENT (Atomic Patches)
```

## 2. Dashboard as a Data Structure

Dashboards are modeled and persisted as pure JSON/relational structures:

- **`Dashboard`**:
  - `id`: UUID
  - `name` / `title`: Human-readable validated title
  - `description`: Analytical context
  - `dataset_id` & `dataset_version_id`: Strict dataset version binding
  - `user_id`: Owner identifier (multi-tenant isolation)
  - `status`: State machine enum (`GENERATING`, `READY`, `PARTIAL`, `FAILED`)
  - `theme`: Design token key (`soft-enterprise`)
  - `layout_type`: Grid system (`12_column_fluid`)
  - `layout_config`: Canvas bounding rules
  - `widgets`: Array of `DashboardWidget`
  - `filters`: Array of `DashboardFilter`
  - `metadata`: Provenance, token metrics, generation stats
  - `created_at`, `updated_at`

- **`DashboardWidget`**:
  - `id`: UUID
  - `dashboard_id`: Foreign key
  - `analysis_id`: Pointer to underlying DuckDB analysis job
  - `widget_type`: `kpi`, `chart`, `table`
  - `title`: Component heading
  - `description`: Narrative explanation
  - `grid_x`, `grid_y`, `grid_w`, `grid_h`: 12-column grid geometry
  - `chart_spec`: Declarative `VisualizationSpec`
  - `result_data`: Cached tabular result subset
  - `analysis_status`: `COMPLETED`, `FAILED`

## 3. Atomic Patch Model

Dashboard updates avoid full state regeneration. The AI Planner and UI emit atomic patches:

| Patch Operation | Parameters | Description |
|---|---|---|
| `ADD_WIDGET` | `widget_plan: DashboardWidgetPlan` | Executes new analytical tool, recommends chart, places in layout |
| `REMOVE_WIDGET` | `widget_id: string` | Deletes widget and reflows layout |
| `MOVE_WIDGET` | `widget_id, grid_x, grid_y` | Validates bounds and collisions, updates position |
| `RESIZE_WIDGET` | `widget_id, grid_w, grid_h` | Enforces column span (3, 4, 6, 8, 12), reflows grid |
| `CHANGE_CHART` | `widget_id, chart_type` | Re-validates against analysis result columns |
| `CHANGE_METRIC` | `widget_id, metric_column` | Re-executes underlying tool with new metric |
| `CHANGE_FILTER` | `filter_id, value` | Updates filter state and propagates to affected widgets |
| `RENAME_DASHBOARD`| `title: string` | Updates sanitized dashboard name |
