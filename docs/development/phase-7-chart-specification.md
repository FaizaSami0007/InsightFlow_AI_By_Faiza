# Phase 7 — Visualization Specification & Schema Model

## VisualizationSpec Schema
The `VisualizationSpec` model defines a structured contract between backend analytical results and frontend chart renderers.

### Schema Fields
- `chart_type`: `bar` | `horizontal_bar` | `line` | `area` | `pie` | `donut` | `scatter` | `histogram` | `boxplot` | `kpi` | `table`
- `title`: Human-readable title derived from analysis operation and column names
- `subtitle`: Analysis lineage and provenance summary (e.g. `Analysis #a1b2c3d4 • Group By`)
- `x_axis`: Column name mapped to horizontal dimension / category / temporal axis
- `y_axis`: Column name or list of measure column names mapped to vertical value axis
- `series`: Optional column name for secondary group by or color categorization
- `sort`: Sort direction (`asc`, `desc`, or `none`)
- `limit`: Optional category limit
- `format`: Display formatting hint (`integer`, `decimal`, `percentage`, `currency`, `compact`)
- `cardinality`: Number of data categories or points
- `options`: Specialized parameters (e.g., `kpi_value`, `kpi_label`, `min`, `q1`, `median`, `q3`, `max`, `bins`)
- `provenance`: `VisualizationProvenance` containing `analysis_id`, `dataset_id`, `dataset_version_id`, `operation`, `row_count`
- `explanation`: Contextual rationale for chart recommendation
- `is_fallback`: Boolean indicating whether the spec was produced as a safe fallback
- `available_chart_types`: Array of compatible alternate chart types available for user switching
