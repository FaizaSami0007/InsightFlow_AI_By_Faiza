# ADR-002 — PostgreSQL + DuckDB

**Decision:** PostgreSQL stores application state; DuckDB performs analytical computation.

**Reason:** Separates transactional concerns from analytical execution and makes the analytical boundary easier to secure and test.
