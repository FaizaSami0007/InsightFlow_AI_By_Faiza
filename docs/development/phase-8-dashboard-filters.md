# Phase 8 — Dashboard Filters & Analytical Propagation

## 1. Filter Model

Filters are declared at the dashboard level and bound to real dataset columns:
- `column_name`: Existing column in dataset
- `display_name`: Formatted UI label
- `filter_type`: `categorical`, `temporal`, `numeric`
- `operator`: `equals`, `in`, `between`, `gte`, `lte`
- `allowed_values`: Top unique distinct values extracted from dataset profile
- `scope`: `global` (all widgets) or `widget` (specific widget IDs)

## 2. Filter Propagation Architecture

When a user selects a filter value (e.g., `Region = "North"`):
1. The frontend dispatches a refresh request: `POST /api/v1/dashboards/{id}/refresh` with `{ filter_values: { "region": "North" } }`.
2. The backend identifies all widgets scoped to this filter.
3. For each widget, the underlying analytical tool is re-executed in DuckDB with a parameterized `WHERE region = 'North'` clause.
4. The new result table updates the widget's cached data and visualization renderer.
5. **No Client-Side Data Masking**: Filtering occurs at the SQL/DuckDB analytical layer to preserve aggregations, percentage calculations, and summary statistics accurately.
