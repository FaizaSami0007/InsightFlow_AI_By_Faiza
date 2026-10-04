# Phase 4 Analytics Tools Catalog

This catalog documents all deterministic analytical tools implemented in Phase 4.

---

## 1. `describe_dataset`
- **Category:** Descriptive Statistics
- **Purpose:** Generates comprehensive summary statistics across all or selected columns.
- **Inputs:** `columns?: string[]`
- **Outputs:** Tabular metrics (Count, Mean, Median, Std Dev, Min, Max, Q1, Q3, IQR, Null Count, Unique Count).
- **Validation:** Column names must exist in dataset schema.

---

## 2. `filter_data`
- **Category:** Filtering
- **Purpose:** Filters dataset rows according to typed comparison conditions and logical operators.
- **Inputs:** `columns?: string[]`, `filters?: FilterCondition | FilterGroup`, `limit?: int`, `offset?: int`
- **Supported Operators:** `=`, `!=`, `>`, `>=`, `<`, `<=`, `IN`, `NOT IN`, `BETWEEN`, `IS NULL`, `IS NOT NULL`, `LIKE`, `ILIKE`.

---

## 3. `sort_data`
- **Category:** Descriptive
- **Purpose:** Sorts rows across one or multiple columns.
- **Inputs:** `sort_by: [{ column: string, order: "ASC" | "DESC" }]`, `columns?: string[]`
- **Validation:** Sort columns must exist in dataset schema.

---

## 4. `group_by`
- **Category:** Aggregation
- **Purpose:** Groups dataset by dimensions and calculates aggregate metrics.
- **Inputs:** `dimensions: string[]`, `aggregations: [{ column: string, agg_type: AggregationType, alias?: string }]`
- **Supported Aggregations:** `SUM`, `AVG`, `MIN`, `MAX`, `COUNT`, `COUNT DISTINCT`, `MEDIAN`, `STDDEV`, `VARIANCE`.
- **Validation:** Numeric aggregations (`SUM`, `AVG`, `MEDIAN`, `STDDEV`, `VARIANCE`) reject non-numeric columns.

---

## 5. `compare_groups`
- **Category:** Aggregation
- **Purpose:** Compares performance of target metrics across distinct segments.
- **Inputs:** `dimension: string`, `metric: string`, `groups?: string[]`, `aggregation?: string`
- **Outputs:** `group_name`, `record_count`, `metric_value`, `delta_from_top`, `percent_difference_from_top`.

---

## 6. `frequency`
- **Category:** Statistical
- **Purpose:** Calculates category counts, proportions, and cumulative frequency percentages.
- **Inputs:** `column: string`, `top_n?: int`
- **Outputs:** `value`, `count`, `percentage`, `cumulative_percentage`.

---

## 7. `correlation`
- **Category:** Statistical
- **Purpose:** Computes Pearson or Spearman pairwise correlation matrix across numeric columns.
- **Inputs:** `columns: string[]` ($\ge 2$), `method?: "pearson" | "spearman"`
- **Validation:** Requires at least 2 numeric columns.

---

## 8. `distribution`
- **Category:** Statistical
- **Purpose:** Calculates distribution shape statistics (skewness, kurtosis) and histogram frequency bins.
- **Inputs:** `column: string`, `bins?: int` (2–50)
- **Outputs:** Histogram bins (`bin_start`, `bin_end`, `count`, `percentage`) + summary moments.

---

## 9. `time_series_summary`
- **Category:** Temporal
- **Purpose:** Rolls up metrics over date truncation intervals.
- **Inputs:** `date_column: string`, `metric_column?: string`, `period: "day" | "week" | "month" | "quarter" | "year"`, `aggregation?: string`
- **Outputs:** `period_bucket`, `record_count`, `metric_total`.

---

## 10. `percent_change`
- **Category:** Temporal
- **Purpose:** Computes sequential delta and period-over-period growth rate.
- **Inputs:** `metric_column: string`, `order_by_column: string`, `group_by_column?: string`
- **Formula:** $\frac{\text{current} - \text{previous}}{|\text{previous}|} \times 100\%$ with zero-division protection.

---

## 11. `outlier_analysis`
- **Category:** Statistical
- **Purpose:** Identifies statistical outliers using Tukey's IQR rule.
- **Inputs:** `column: string`, `multiplier?: float` (default 1.5)
- **Thresholds:** Lower bound $Q1 - 1.5 \times IQR$, Upper bound $Q3 + 1.5 \times IQR$.
