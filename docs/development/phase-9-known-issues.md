# Phase 9: Known Issues & Deferred Capabilities

## 1. Known Limitations

1. **Complex Chart Interactive Rendering in Headless PDF:**
   - PDF exports rely on ReportLab vector graphics and structured data tables. Interactive tooltips or hover animations from Recharts in the browser are by design omitted from static PDF prints.
2. **Synchronous File Generation for Standard Dashboards:**
   - For typical dashboards (<= 15 widgets), generation takes under 200 ms. For extremely large dashboards, async job polling can be enhanced with Redis/Celery in future scaling phases.

---

## 2. Deferred Capabilities (Explicitly Out of Scope for Phase 9)

- **No Multi-Dataset Federation:** Cross-dataset joining across heterogeneous external databases is deferred to a future dedicated phase.
- **No Vector DB / RAG / Embeddings:** Reporting uses deterministic analytics and validated specifications.
- **No Autonomous Agent Swarms:** Exports are deterministic, rule-based, and user-initiated.
- **No Embedded Password Protection for Shares:** Basic link tokenization is implemented; per-link custom password hashing can be introduced if enterprise requirements dictate.
