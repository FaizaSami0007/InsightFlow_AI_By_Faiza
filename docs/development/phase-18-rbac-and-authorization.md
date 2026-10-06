# Phase 18 — RBAC & Authorization Architecture

## 1. 5-Tier Role Hierarchy
InsightFlow AI defines five deterministic enterprise roles:
- `OWNER`: Full platform administration, security management, billing, and organizational ownership.
- `ADMIN`: Tenant configuration, security audit inspection, connector management, model lifecycle approvals.
- `ANALYST`: Dataset creation, query execution, model training & deployment, report creation & export.
- `MEMBER`: Dataset exploration, model metrics viewing, knowledge center access, report viewing.
- `VIEWER`: Strictly read-only access to published dashboards, forecasts, and dataset schemas.

## 2. Server-Side Enforcement
FastAPI dependencies (`require_permission(permission)` and `require_role([roles])`) enforce claims before any service handler executes. Implicit trust is strictly rejected.
