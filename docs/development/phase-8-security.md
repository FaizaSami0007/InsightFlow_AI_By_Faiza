# Phase 8 — Security & Authorization Guarantees

## 1. Multi-Tenant Dashboard Ownership

- Dashboards are strictly owned by `user_id`.
- `DashboardService` queries always filter by `user_id` and raise `HTTPException(404)` or `HTTPException(403)` on cross-tenant access.
- Deletion and patch applications verify ownership before executing any database modifications.

## 2. Dataset Authorization Parity

- A dashboard referencing Dataset `D` requires the requesting user to hold valid read permissions on `D`.
- Refresh and patch operations re-verify dataset access before running analytical tools.

## 3. No Code Execution / XSS Prevention

- The AI planner only returns structured JSON plans.
- Frontend renders purely declarative Recharts and table components with sanitized text labels.
- No HTML, SVG strings, JavaScript callbacks, or executable scripts are accepted or rendered.

## 4. Resource & Rate Limiting

- Hard limit of 12 widgets per dashboard.
- Maximum 10 filters per dashboard.
- Analytical execution graph operates under query timeout limits (15 seconds per tool invocation).
