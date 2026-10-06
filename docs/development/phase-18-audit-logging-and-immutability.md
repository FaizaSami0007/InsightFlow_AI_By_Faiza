# Phase 18 — Security Audit Logging & Immutability

## 1. Audit Trail Architecture
`SecurityAuditLog` captures identity, authorization, resource modification, and attack mitigation events in an append-only ledger:
- Actor ID, email, and active role
- Action type (`LOGIN_SUCCESS`, `PROMPT_INJECTION_BLOCKED`, `DATASET_CREATED`, etc.)
- Target resource type and resource ID
- Client IP address and User Agent
- Correlation ID (`X-Request-ID`)
- Sanitized detail payload with automated password/token/key redaction

## 2. Immutability & Access Governance
Audit log query endpoints (`/api/v1/security/audit-logs`) require explicit `SECURITY_AUDIT_VIEW` permission (granted only to `ADMIN` and `OWNER` roles). Normal users and background jobs cannot alter or delete audit history.
