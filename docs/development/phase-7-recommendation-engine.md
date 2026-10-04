# Phase 7 — Deterministic Recommendation Engine & Suitability Rules

## Chart Suitability Engine
The `RecommendationEngine` evaluates analytical operation metadata, result row cardinality, inferred axis data types, and value properties to choose the most readable and truthful chart representation.

### Suitability Rules Summary

| Result Schema / Intent | Selected Chart Type | Alternative Compatible Types |
| :--- | :--- | :--- |
| **Single Scalar Metric** (1 row, 1 measure) | `kpi` | `table` |
| **Statistical Five-Number Summary** (Q1, median, Q3, min, max) | `boxplot` | `histogram`, `table` |
| **Binned Numerical Distribution** (Intervals + Counts) | `histogram` | `bar`, `table` |
| **Temporal Trend** (Date/Timestamp + 1+ Measures) | `line` | `area`, `bar`, `table` |
| **Correlation** (2 Numeric Columns, No Dimension) | `scatter` | `table` |
| **Small Categorical Composition** (3–6 non-negative categories, short labels) | `donut` | `pie`, `bar`, `horizontal_bar`, `table` |
| **Categorical Comparison with Long Labels** (> 12 chars avg) | `horizontal_bar` | `bar`, `table` |
| **Categorical Comparison** (<= 20 categories) | `bar` / `horizontal_bar` | `donut`, `pie`, `table` |
| **High Cardinality / Multi-dimensional Matrix** (> 20 categories) | `table` | `bar` (top-N) |

### Cardinality Thresholds
- `MAX_PIE_CATEGORIES = 6` (values must be strictly non-negative)
- `MAX_BAR_CATEGORIES = 20`
- `MIN_HISTOGRAM_VALUES = 10`
- `MAX_SCATTER_POINTS = 500`
