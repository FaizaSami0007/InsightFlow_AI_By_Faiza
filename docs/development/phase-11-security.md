# Phase 11: Forecasting Security & Safety

## 1. Multi-Tenant Authorization & IDOR Defenses
- Users can only run forecasts against datasets they own or have explicit authorized access to.
- Cross-tenant requests produce HTTP 403 Forbidden or 404 Not Found.
- Background tasks and forecast database records are strictly partitioned by user UUID.

## 2. Resource Exhaustion & Denial of Service Defenses
- `MAX_FORECAST_HORIZON = 100` (default maximum is capped to prevent memory explosion).
- `MAX_TRAINING_ROWS = 50,000` (capped DuckDB query buffer).
- `MIN_OBSERVATIONS = 6` (prevents degenerate matrix inversion in autoregressive estimation).
- Bounded ARIMA order space (max $p=2, d=1, q=1$) prevents computational timeouts.

## 3. Anti-Injection & Sandboxing
- Dynamic SQL queries use parameterization and sanitized double-quoted column identifiers (`TRY_CAST("{col}" AS DOUBLE)`).
- Model parameters are bounded enums and numeric primitives; user inputs never reach Python `eval()`, `exec()`, or dynamic imports.
- AI tool calls are validated against Pydantic schemas before reaching the ML execution service.
