# Phase 8 — AI Dashboard Planner & Plan Validator

## 1. Role & Responsibilities

The AI Dashboard Planner translates analytical intent and dataset semantics into a verified `DashboardPlan`.
It operates under strict constraints:
- Minimum widgets: 2, Maximum widgets: 12 (default 5–8)
- Grounded in semantic metadata (`MEASURE`, `DIMENSION`, `TEMPORAL`, `IDENTIFIER`)
- Data quality aware: downweights high-missingness or constant fields
- Redundancy detection: rejects duplicate (dimension, metric) pairings

## 2. Dashboard Plan Schema

```json
{
  "title": "Sales Performance Overview",
  "purpose": "sales",
  "dataset_id": "ds-1234",
  "dataset_version_id": "ver-5678",
  "widgets": [
    {
      "title": "Total Revenue",
      "widget_type": "kpi",
      "operation": "summary",
      "params": {"column": "revenue", "aggregations": ["sum"]},
      "preferred_chart_type": "kpi",
      "grid_w": 4,
      "grid_h": 2
    },
    {
      "title": "Monthly Revenue Trend",
      "widget_type": "chart",
      "operation": "time_series",
      "params": {"date_column": "order_date", "metric_column": "revenue", "period": "month"},
      "preferred_chart_type": "line",
      "grid_w": 8,
      "grid_h": 4
    }
  ],
  "suggested_filters": ["region", "order_date"],
  "reasoning_summary": "Constructed 4-widget sales view emphasizing core revenue KPIs and regional breakdown."
}
```

## 3. Plan Validation Rules

Every plan is checked deterministically before executing analytical computations:
1. **Tool Availability**: `operation` must map to a registered `AnalyticsTool` (`summary`, `group_by`, `time_series`, `frequency`, `correlation`).
2. **Column Grounding**: All referenced columns must exist in the dataset profile schema.
3. **Semantic Matching**: Measures must be numeric; temporal charts must reference valid temporal/datetime fields.
4. **Widget Caps**: Plans with >12 widgets are rejected or trimmed to 12.
5. **Anti-Redundancy**: Consecutive duplicate metric/dimension pairs are pruned.
