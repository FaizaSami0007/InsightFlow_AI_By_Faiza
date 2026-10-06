# Phase 17 — Testing Suite & Security Validation

## Test Organization
Phase 17 includes comprehensive unit, integration, and security test coverage in:
- `apps/api/tests/test_connectors.py`
- `apps/api/tests/test_phase17_evaluation.py`

### 1. Security Tests
- **SSRF Attack Vectors:** 15 adversarial URLs targeting private RFC-1918 subnets (`10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`), loopback (`127.0.0.1`), link-local metadata (`169.254.169.254`), and forbidden schemes (`file://`, `ftp://`, `gopher://`).
- **SQL Injection Defense:** 15 destructive SQL queries (`DROP`, `DELETE`, `ALTER`, `TRUNCATE`, `EXEC`, multi-statement injections) blocked by `SQLSafetyValidator`.
- **Credential Masking & Encryption:** Verified that credentials undergo Fernet symmetric encryption and are strictly masked (`********`) in responses.
- **IDOR Multi-Tenant Isolation:** Cross-tenant connection access and schema discovery verified to return 404/forbidden.

### 2. Lifecycle Integration Tests
- End-to-end SQLite connector discovery, preview sampling, record ingestion, dataset version creation, DuckDB profiling, and audit logging.
