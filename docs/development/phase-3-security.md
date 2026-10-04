# Phase 3 Security & Access Control Specifications

## 1. Multi-Tenant Dataset Isolation
All profiling, quality, semantic override, and query endpoints require authenticated JWT bearer tokens (`get_current_user`). Dataset ownership is validated against `dataset.owner_id == current_user.id`. Cross-user access returns HTTP 404 / Unauthorized.

## 2. SQL Injection & Execution Hardening
- Parameterized binding for analytical parameters.
- Static regex analysis of SQL queries before execution in DuckDB.
- Single-statement isolation preventing chained command injection.
- Direct filesystem operations via DuckDB are strictly blocked.

## 3. Storage Traversal Defenses
Storage keys use generated UUIDs. Physical path lookups verify that the target path resides strictly inside `settings.data_dir`.
