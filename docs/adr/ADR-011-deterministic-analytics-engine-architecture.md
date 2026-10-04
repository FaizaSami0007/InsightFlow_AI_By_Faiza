# ADR-011: Deterministic Analytics Engine and Analysis Registry Architecture

## Status
Accepted

## Context
InsightFlow AI requires a mathematically accurate, deterministic analytics engine for aggregations, descriptive statistics, group comparisons, correlation matrices, and time series trends. The system must never rely on LLM guessing or unvalidated SQL strings for numerical calculations.

## Decision
1. **Centralized Analysis Registry:** All analytical operations are encapsulated as distinct `AnalysisTool` instances with strict input/output contracts and parameter schemas.
2. **Safe SQL Builder:** Dynamic query generation uses parameterized predicates, identifier whitelisting against known dataset schemas, and read-only statement enforcement.
3. **Execution Layer:** DuckDB in-process virtual views execute high-performance analytical queries.
4. **Result Sanitization & Provenance:** Output payloads are sanitized against `NaN`/`Infinity` values, and every analysis records immutable provenance linking to the exact dataset version ID and parameters.

## Consequences
- 100% deterministic, reproducible analytical results.
- Clean contract for future AI agents (Phase 5) to discover and call tools without guessing or fabricating data.
- Strict isolation and protection against SQL injection and multi-tenant data leakage.
