# Phase 7 — Visualization Testing & Evaluation Suite

## Test Coverage Summary

Phase 7 is covered by dedicated test suites testing rule evaluation, schema validation, API security, and conversational visual follow-ups:

### 1. Recommendation Engine Unit Suite (`tests/test_visualization_recommendation.py`)
- Single scalar metric -> `kpi`
- Time-series data -> `line` / `area`
- Small categorical composition (3–6 non-negative categories) -> `donut` / `pie`
- Moderate categories (<= 20) -> `bar` / `horizontal_bar`
- Long category labels (> 12 chars) -> `horizontal_bar`
- Correlation (2 numerics) -> `scatter`
- Five-number summary distribution -> `boxplot`
- High cardinality (> 20 categories) -> `table` fallback
- User preference override within compatible chart types

### 2. Chart Validator Unit Suite (`tests/test_visualization_validator.py`)
- Accepts valid specifications
- Rejects non-existent columns with automatic safe fallback
- Rejects invalid data types on axes (e.g. string Y-axis on Bar chart)
- Rejects pie charts exceeding cardinality thresholds (> 6 categories)
- Rejects pie charts with negative values
- Rejects XSS and `<script>` injection attempts in title, subtitle, and explanation

### 3. Visualization API Integration Suite (`tests/test_visualization_api.py`)
- `GET /api/v1/visualizations/charts`: metadata listing
- `POST /api/v1/visualizations/recommend`: recommendation generation
- `POST /api/v1/visualizations/validate`: specification validation
- Cross-tenant access isolation verification (User B cannot access User A's analysis visualization)

### 4. Conversational Visual Follow-up Suite (`tests/test_conversational_visualization.py`)
- Analytical question generates grounded answer + attached visualization
- Visual follow-up "Make it horizontal" updates chart presentation to `horizontal_bar` without altering data
- Visual follow-up "Display it as a table" switches to `table` view
- Visual follow-up "Show this as a bar chart" restores `bar` presentation
- Full provenance tracing: analysis ID, dataset ID, dataset version ID
