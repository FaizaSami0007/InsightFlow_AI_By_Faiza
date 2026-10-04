# ADR-008: Backend Foundation, Standardized Error Model, and Structured Logging

## Status
Accepted (Phase 1)

## Context
InsightFlow AI requires a robust, observable, and modular backend foundation capable of supporting deterministic analytical execution, data lineage, and AI orchestration without leaking secrets, internal implementation details, or unstructured stack traces to clients.

## Decision
1. **Modular Monolith Layout**: The FastAPI backend is structured into decoupled domain namespaces (`users`, `datasets`, `analytics`, `ai`, `dashboards`, `conversations`, `shared`) under a centralized core (`core/config.py`, `core/logging.py`, `core/security.py`, `core/error_handlers.py`).
2. **Standardized Error Envelope**: All API exceptions (domain exceptions, validation errors, HTTP exceptions, unexpected server errors) map to a uniform JSON error contract:
   ```json
   {
     "error": {
       "code": "ERROR_CODE",
       "message": "Human-readable explanation",
       "details": {},
       "request_id": "uuid-v4"
     }
   }
   ```
3. **Structured Context Logging & Redaction**: Every request receives a unique `X-Request-ID` tracked across async execution contexts via `contextvars`. Sensitive keys (`password`, `secret`, `token`, `api_key`, `authorization`) are scrubbed before writing to logs.
4. **Asynchronous Database Session Management**: SQLAlchemy 2.0 async engine (`postgresql+asyncpg`) and async sessionmakers provide non-blocking I/O. Database schema migrations are governed by Alembic.
5. **Two-Tier Health Probes**:
   - `GET /api/v1/health`: Lightweight liveness check returning uptime and service metadata.
   - `GET /api/v1/health/ready`: Readiness probe verifying database connectivity (`SELECT 1`).

## Consequences
- Error handling is consistent across all future modules.
- Debugging is streamlined via correlatable `X-Request-ID` headers in logs and responses.
- Eliminates accidental credential leakage in log streams.
