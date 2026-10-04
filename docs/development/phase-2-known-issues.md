# Phase 2 — Known Issues & Deferred Features

**Date:** 2026-10-04  
**Status:** All Phase 2 Quality Gates Passed  

---

## 1. Known Environment Limitations

1. **Host Docker CLI Availability:**
   - Docker CLI is not present in the Windows host PATH. Docker Compose configurations (`docker-compose.yml`) remain syntactically validated.

---

## 2. Intentionally Deferred Items (Phase Boundaries)

| Capability | Target Phase | Rationale |
|---|---|---|
| **Data Profiling & Quality Scoring** | Phase 3 | Statistical column analysis, missing value detection, outlier scores, and PII masking belong to the Data Engineering phase. |
| **Deterministic Analytics (DuckDB/Polars)** | Phase 4 | In-memory aggregations, group-by queries, correlations, and read-only SQL sandboxing belong to Phase 4. |
| **AI Analyst & Tool Calling** | Phase 5 | LLM prompt orchestration and tool allowlist validation belong to Phase 5. |
| **Visualization & Chart Rendering** | Phase 6 | KPI cards, bar charts, line plots, and scatter renderings belong to Phase 6. |
| **Dashboard Builder** | Phase 7 | Dashboard layout JSON persistence and NL dashboard editing belong to Phase 7. |
| **Refresh Tokens & Server-Side Token Blacklisting** | Phase 8 (Hardening) | Currently, stateless short-lived access tokens with client-side disposal are implemented. Full Redis-backed token revocation will be added during production hardening. |
