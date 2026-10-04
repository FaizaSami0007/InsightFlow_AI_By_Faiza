# ADR-010: Polars for Profiling and DuckDB for Analytical Execution

## Status
Accepted

## Context
InsightFlow AI requires deterministic dataset profiling and fast analytical query processing without overloading the primary PostgreSQL application metadata database.

## Decision
- **Polars** is utilized as the primary in-memory dataframe engine for scanning files, detecting schemas, computing exact quartiles, percentiles, and outlier detection.
- **DuckDB** is deployed as the in-memory SQL analytical engine for queries, aggregations, filtering, and group-by execution.
- **PostgreSQL** remains the system of record for user identity, dataset version metadata, and persisted profiling results.

## Consequences
- High-performance, deterministic execution without requiring external computation clusters.
- Clear separation of concerns between relational metadata (PostgreSQL) and analytical computing (DuckDB & Polars).
