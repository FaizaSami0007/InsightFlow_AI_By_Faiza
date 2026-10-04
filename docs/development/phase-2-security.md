# Phase 2 — Security Implementation & Threat Mitigation

**Date:** 2026-10-04  
**Scope:** Identity & Authentication, File Ingestion Security  

---

## 1. Authentication & Token Security

- **Password Hashing**: Passwords are never stored in plaintext. They are hashed using `bcrypt` via Passlib with automatic salt generation.
- **JWT Cryptographic Integrity**: Access tokens are signed using `HMAC-SHA256` (`HS256`). Claims are strictly minimized to `sub`, `exp`, `iat`, `jti`, and `type="access"`. No sensitive personal data is stored in JWT payloads.
- **Environment Secret Enforcement**: In `production` environments, the application fails to start if `JWT_SECRET` is shorter than 32 characters or matches insecure development placeholders.
- **Protected Endpoint Authorization**: All `/datasets` endpoints require the `get_current_user` FastAPI dependency. Unauthenticated requests are rejected with HTTP 401.

---

## 2. Server-Side Ownership Isolation

- **Zero Client-Side Trust**: Dataset queries explicitly filter by `Dataset.owner_id == current_user.id`.
- **Authorization Enforcement**: If User B attempts to access `/api/v1/datasets/{dataset_id}` where `dataset_id` is owned by User A, the server returns HTTP 403 / 404. Information regarding foreign datasets is never leaked.

---

## 3. Untrusted File Ingestion & Storage Defense

- **Path Traversal Mitigation**: File storage identifiers are generated as UUID hex strings (e.g. `d7a31b4e...csv`). Original user filenames are never used in filesystem path construction.
- **MIME & Magic Byte Verification**:
  - Parquet files must start with the standard `PAR1` magic bytes.
  - CSV files must parse as valid UTF-8 tabular streams with headers.
- **Denial of Service (DoS) / Upload Limits**:
  - Configurable maximum upload limit (`MAX_UPLOAD_SIZE_MB`, default 50 MB) enforced prior to parsing.
  - Empty files are rejected (HTTP 422).
- **Integrity & Provenance (SHA-256)**:
  - Every uploaded version computes a SHA-256 cryptographic digest stored in the database for integrity validation and provenance tracking.
- **Transaction Failure Cleanup**:
  - If a database transaction fails during dataset creation, the stored file is removed immediately from disk to prevent orphan storage leaks.
