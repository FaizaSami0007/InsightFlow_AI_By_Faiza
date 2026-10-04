# Phase 3 DuckDB Analytical Execution Engine

## 1. Role & Responsibility
DuckDB serves as the in-memory analytical compute engine for fast aggregation, filtering, and structured query execution. PostgreSQL retains application state and metadata, while DuckDB performs analytical queries.

## 2. Dataset Virtual Views
- Datasets are registered as virtual views (`CREATE OR REPLACE VIEW tbl_<version_clean_id> AS SELECT * FROM read_csv_auto(...)` or `read_parquet(...)`).
- User SQL can reference `dataset` or `data`, which the manager safely rewrites to the internal view identifier.

## 3. SQL Safety Boundary
- Read-only enforcement (`SELECT` and `WITH` only).
- Prohibited operations: `CREATE`, `DROP`, `ALTER`, `INSERT`, `UPDATE`, `DELETE`, `ATTACH`, `LOAD`, `INSTALL`, `COPY`, `EXPORT`, `IMPORT`, `PRAGMA`, `CALL`, `SYSTEM`.
- Multi-statement injection rejection (semicolon detection).
- Automatic result row limit clamping (`MAX_RESULT_ROWS = 1000`).
