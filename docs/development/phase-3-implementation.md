# Phase 3 Implementation Specification: Data Profiling, Quality, Semantic Layer & DuckDB

**Scope:** Deterministic Data Profiling, Quality Scoring, Semantic Metadata Classification & DuckDB Analytical Engine  
**Status:** Completed & Verified  

---

## 1. Architecture Overview

Phase 3 introduces the deterministic analytical foundation for InsightFlow AI. The system operates strictly deterministically without LLM guessing, providing verified structural, statistical, and semantic facts across tabular datasets.

```
┌────────────────────────────────────────────────────────┐
│                   Immutable DatasetVersion             │
└───────────────────────────┬────────────────────────────┘
                            │
              ┌─────────────▼────────────┐
              │    DataReader Factory    │
              │  (CSV / Parquet Reader)  │
              └─────────────┬────────────┘
                            │
              ┌─────────────▼────────────┐
              │     Profiling Engine     │
              │ (Polars Statistical Scan)│
              └──────┬──────┬──────┬─────┘
                     │      │      │
       ┌─────────────┘      │      └─────────────┐
       ▼                    ▼                    ▼
┌──────────────┐    ┌──────────────┐     ┌──────────────┐
│ Data Quality │    │  Semantics   │     │    DuckDB    │
│  Evaluation  │    │Classification│     │ Registration │
│(Score & Warn)│    │(Role & Conf) │     │ (Safe Views) │
└──────┬───────┘    └──────┬───────┘     └──────┬───────┘
       │                   │                    │
       └─────────────┬─────┴────────────────────┘
                     │
              ┌──────▼───────────┐
              │ PostgreSQL Schema│
              │  (Persistence)   │
              └──────────────────┘
```

---

## 2. Core Subsystems

### A. Data Readers (`app/profiling/readers/`)
- **`DataReader` Abstract Base Class**: Standard interface for schema inspection, bounded/unbounded dataframe loading, sampling, and row counting.
- **`CSVDataReader`**: Automatic delimiter detection (`,`, `\t`, `;`, `|`), schema inference length (10,000 rows), date parsing heuristics.
- **`ParquetDataReader`**: Native schema extraction and columnar batch loading.
- **`get_data_reader(format)`**: Factory returning the appropriate format reader.

### B. Profiling Engine (`app/profiling/engine/`)
- High-performance Polars execution calculating:
  - **Dataset-level**: `row_count`, `column_count`, `memory_size_bytes`, `duplicate_rows`, `duplicate_percentage`, `duration_ms`.
  - **Column normalization**: Original name preserved, normalized snake_case name generated.
  - **Type Mapping**: Mapping Polars dtypes to standardized `ConceptualType` (`STRING`, `INTEGER`, `FLOAT`, `BOOLEAN`, `DATE`, `DATETIME`, `TIME`, `UNKNOWN`).
  - **Numeric profiling**: Count, min, max, mean, median, standard deviation, variance, quartiles (Q1, Q2, Q3), IQR, and percentiles (P01, P05, P10, P25, P50, P75, P90, P95, P99).
  - **Outlier detection**: Tukey's IQR rule: $[Q1 - 1.5 \times IQR, Q3 + 1.5 \times IQR]$.
  - **Categorical profiling**: Top frequent values with counts and percentages, cardinality ratio.
  - **Temporal & Boolean profiling**: Min/max boundaries, boolean truth distribution.

### C. Data Quality Engine (`app/profiling/quality/`)
- Computes an explainable, transparent quality score (0.0 – 100.0) and letter grade (A/B/C/D/F) with penalty weights:
  - Missingness penalty ($w=0.35$)
  - Duplicate penalty ($w=0.25$)
  - Constant column penalty ($w=0.20$)
  - Outlier penalty ($w=0.20$)
- Categorizes missingness into 5 standard buckets (0%, 0-5%, 5-20%, 20-50%, >50%).
- Emits structured warnings feed with severity levels (`ERROR`, `WARNING`, `INFO`).

### D. Semantic Layer (`app/profiling/semantics/`)
- Heuristically infers analytical roles:
  - `MEASURE` (Numeric continuous metrics, currency indicators)
  - `DIMENSION` (Categorical groupings, geographic attributes)
  - `IDENTIFIER` (UUIDs, integer keys, tracking IDs)
  - `DATE` / `DATETIME` (Temporal timestamps)
  - `BOOLEAN` (Binary flags)
- Computes inference confidence score (0.0 to 1.0).
- Separates system inference from user definition (`inferred_role` vs `user_role`).

### E. DuckDB Analytical Layer (`app/analytics/duckdb/`)
- Thread-safe `DuckDBManager` executing analytical queries over virtual dataset views.
- Strict security validation: Read-only enforcement (`SELECT` / `WITH` only), rejection of destructive DDL/DML and multi-statement queries.
- Bounded result limits (`MAX_RESULT_ROWS = 1000`).
- Query plan inspection (`EXPLAIN`) and connection health checks.

---

## 3. Database Persistence & Lineage

All profile results are linked immutably to a specific `dataset_version_id`:
- `dataset_profiles` (Status, counts, timing)
- `column_profiles` (Per-column stats and distributions)
- `data_quality_reports` (Quality score, penalty breakdown, warnings)
- `semantic_columns` (Semantic roles, flags, user overrides)

Lineage is guaranteed: uploading a new dataset version creates a fresh, isolated profile without corrupting earlier versions.
