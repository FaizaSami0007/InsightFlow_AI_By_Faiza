# Phase 9: Secure Dashboard Sharing Engine

## 1. Overview

InsightFlow AI supports controlled, tokenized dashboard sharing that allows authorized external viewers to inspect validated dashboards without accessing raw database connections or the dashboard owner's credentials.

---

## 2. Sharing Modes

1. **Live Analytical Sharing (`is_snapshot = False`):**
   - Re-runs authenticated analytical queries against DuckDB for authorized widgets.
   - Allows viewers to interactively filter by columns declared in `allowed_filters`.
   - Viewer filtering creates a session-isolated query state that **never** modifies the owner's stored dashboard specification.
2. **Frozen Static Snapshot Sharing (`is_snapshot = True`):**
   - Serializes and stores a point-in-time snapshot of the dashboard specification, widget metrics, and tabular rows in `snapshot_data`.
   - Guaranteed reproducibility even if the underlying dataset is updated or modified.

---

## 3. Token Security & Lifecycle

- **Token Generation:** Cryptographically strong 256-bit URL-safe random tokens generated via `secrets.token_urlsafe(32)`.
- **Expiration Policy:** Configurable expiration intervals (1 day, 7 days, 30 days, 90 days, or null for indefinite).
- **Immediate Revocation:** Owners can revoke share access instantaneously via `DELETE /api/v1/shares/{id}`. Revoked tokens immediately return HTTP 404 to all subsequent viewer requests.
- **Audit & Metrics:** Access timestamps (`last_accessed_at`) and viewer counters (`view_count`) are automatically incremented on each legitimate access.
