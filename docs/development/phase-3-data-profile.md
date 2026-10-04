# Phase 3 Data Profiling Specification

## 1. Overview
The data profiling engine in InsightFlow AI provides deterministic mathematical and structural analysis of tabular datasets (CSV and Parquet).

## 2. Statistical Pipeline
1. **Schema & Dtype Mapping**: Polars data types are mapped to `ConceptualType` (`INTEGER`, `FLOAT`, `STRING`, `BOOLEAN`, `DATE`, `DATETIME`, `TIME`, `UNKNOWN`).
2. **Descriptive Statistics**:
   - Numeric: Count, Mean, Median, Min, Max, Standard Deviation, Variance.
   - Quartiles & Percentiles: Q1, Q2, Q3, IQR, P01, P05, P10, P25, P50, P75, P90, P95, P99.
   - Outliers: Tukey IQR Method ($[Q1 - 1.5 \times IQR, Q3 + 1.5 \times IQR]$).
3. **Categorical Analysis**:
   - Cardinality ratio: $\text{uniques} / \text{non-null count}$.
   - Top 10 frequent values with count and percentage.
4. **Temporal & Boolean Analysis**:
   - Boundary extraction (min/max date).
   - Boolean truth value count and percentage distribution.
