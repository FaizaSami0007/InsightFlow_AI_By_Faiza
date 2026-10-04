# Phase 1 — Known Issues & Limitations

**Date:** 2026-10-04  
**Status:** All Phase 1 Quality Gates Passed

---

## 1. Environment & Tooling Constraints

1. **Docker CLI Host Availability:**
   - The host system does not have the `docker` binary in its Windows command path.
   - `docker-compose.yml` is defined and verified syntactically for PostgreSQL and Redis services, but container startup requires Docker Desktop to be installed/running on the developer machine.
   - *Impact on Phase 1:* None. The SQLite in-memory and mocked database health checks validate the application code independently.

---

## 2. Intentionally Deferred Items (Phase Boundaries)

The following capabilities are deliberately deferred to subsequent development phases according to the master roadmap:

| Domain | Deferred Capability | Target Phase |
|---|---|---|
| **Identity** | User registration, login endpoint, JWT issuance/verification, password hashing | Phase 2 |
| **Data Ingestion** | File upload handlers (multipart CSV/Parquet), schema inference, dataset storage | Phase 2 |
| **Data Quality** | Profiling engine, null ratio detection, outlier analysis, PII masking | Phase 3 |
| **Analytics Engine** | Embedded DuckDB query execution, aggregation/group-by engines, provenance logging | Phase 4 |
| **AI Orchestration** | Gemini/LLM provider integration, analysis plan generator, tool allowlist authorization | Phase 5 |
| **Visualization** | Chart renderers (KPI, bar, line, scatter, table), Vega/Recharts component tree | Phase 6 |
| **Dashboards** | Context-aware dashboard layout builder, JSON persistence, natural language editing | Phase 7 |
| **Hardening** | Production rate limiting, distributed telemetry (OTel), backup automation | Phase 8 |

---

## 3. Resolved Phase 1 Baseline Issues

1. `ModuleNotFoundError: No module named 'app'` resolved by configuring `pythonpath = ["."]` in `pyproject.toml`.
2. Python import sorting and unused imports resolved via `ruff check --fix` and `ruff format`.
3. ESLint configuration created (`.eslintrc.json`) allowing Next.js 15 linting to run non-interactively.
4. TypeScript path aliases (`@/*`) configured in `tsconfig.json`.
