# Phase 4 Security & Access Control Specifications

## 1. Multi-Tenant Authorization Enforcement
- All analytics operations (`POST /api/v1/analytics/run`, `GET /api/v1/analytics/{id}`, `GET /api/v1/analytics/history`) require authenticated JWT Bearer tokens.
- Cross-tenant access is strictly blocked: The database query enforces `Dataset.owner_id == current_user.id`. Any attempt by User B to analyze User A's dataset returns `404 Not Found`.

## 2. SQL Safety & Injection Defense
- **Identifier Whitelisting:** All column identifiers are verified against the registered dataset schema (`dataset.columns`) before SQL assembly.
- **Identifier Quoting:** Identifiers are escaped with double quotes (`"column_name"`).
- **Parameterized Predicates:** User-supplied filter comparison values are strictly passed as positional parameters (`?`) to DuckDB.
- **Read-Only Execution:** Non-SELECT statements (`INSERT, UPDATE, DELETE, DROP, ALTER, CREATE, ATTACH, INSTALL, LOAD, PRAGMA`) and multi-statement queries (`semicolons`) are rejected with `DuckDBSecurityError`.

## 3. Resource Bounds
- Output result rows are capped at `MAX_RESULT_ROWS = 1000` (configurable up to `10000`).
- Query execution timeout prevents runaway queries.
