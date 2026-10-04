# Phase 2 — Implementation Summary

**Date:** 2026-10-04  
**Scope:** Identity & Authentication, Dataset Ingestion & Versioning  

---

## 1. Overview

Phase 2 introduces the complete identity, session management, and dataset ingestion foundation for InsightFlow AI. Users can register, log in, manage authentication tokens, and upload structured CSV and Parquet files. Uploads are strictly validated, checksummed using SHA-256, versioned transactionally, and isolated by user ownership server-side.

---

## 2. Identity & Authentication (`apps/api/app/users/`)

### Architecture & Security
- **`app/database/models/user.py`**: User model with `id` (UUIDv4), `email` (indexed, unique constraint), `password_hash` (bcrypt), `full_name`, `is_active`, and cascade relationship to datasets.
- **`app/users/security.py`**:
  - `hash_password(password)` and `verify_password(plain, hashed)` using `passlib[bcrypt]`.
  - `create_access_token(data, expires_delta)`: generates signed JWT bearer tokens with `sub`, `exp`, `iat`, `jti`, and `type="access"`.
  - `decode_access_token(token)`: verifies signature, expiration, and algorithm against `settings.jwt_secret`.
- **`app/users/schemas.py`**: Pydantic schemas for `UserCreate`, `LoginRequest`, `UserResponse`, and `TokenResponse` with password strength rules and email normalization.
- **`app/users/dependencies.py`**: Reusable `get_current_user` dependency reading bearer headers, decoding claims, resolving the user in the database, and checking `is_active`.
- **`app/users/router.py`**:
  - `POST /api/v1/auth/register` (201 Created)
  - `POST /api/v1/auth/login` (200 OK -> JWT TokenResponse)
  - `GET /api/v1/auth/me` (200 OK -> User profile)
  - `POST /api/v1/auth/logout` (200 OK)

---

## 3. Dataset Ingestion & Versioning (`apps/api/app/datasets/`)

### Data Model & Lifecycle
- **`app/database/models/dataset.py`**:
  - `Dataset`: `id`, `owner_id` (FK to `users.id`), `name`, `description`, `status` (`UPLOADING`, `VALIDATING`, `READY`, `FAILED`, `ARCHIVED`), `created_at`, `updated_at`.
  - `DatasetVersion`: `id`, `dataset_id` (FK to `datasets.id`), `version_number` (int, 1, 2, ...), `file_name`, `file_format` (`CSV`, `PARQUET`), `file_size`, `storage_reference`, `checksum` (SHA-256), `status`, `row_count`, `column_count`.
  - Unique constraint: `(dataset_id, version_number)`.

### Storage Abstraction & Path Traversal Defense
- **`app/datasets/storage.py`**:
  - `StorageProvider` protocol with `LocalStorageProvider` implementation.
  - Generates unique UUID keys on disk (e.g. `e5a8f4c...csv`), preventing directory traversal and filename collision attacks.
  - Automatic directory resolution and cleanup of orphaned files on transaction failures.

### File Validation
- **`app/datasets/validator.py`**:
  - CSV: Validates UTF-8 encoding, non-empty content, tabular parsing using Polars, and column header presence.
  - Parquet: Validates `PAR1` magic bytes and tabular metadata readability.
  - Size check against configurable `MAX_UPLOAD_SIZE_MB` (50 MB default).
  - SHA-256 cryptographic checksum calculation for provenance and deduplication.

### Endpoints
- `POST /api/v1/datasets`: Multipart upload creating Dataset and Version 1.
- `POST /api/v1/datasets/{dataset_id}/versions`: Multipart upload adding Version `N+1`.
- `GET /api/v1/datasets`: Paginated listing of user's datasets (`?page=1&page_size=20`).
- `GET /api/v1/datasets/{dataset_id}`: Dataset metadata and version history.
- `GET /api/v1/datasets/{dataset_id}/versions`: List of immutable version records.
- `GET /api/v1/datasets/{dataset_id}/download`: Authenticated file download stream.

---

## 4. Frontend Implementation (`apps/web`)

- **Auth Store (`src/stores/use-auth-store.ts`)**: State management for user profile, JWT storage in `localStorage`, login, register, and logout.
- **Centralized API Client (`src/lib/api-client.ts`)**: Automatic `Authorization: Bearer <token>` injection on all API calls and multipart upload helper `api.upload`.
- **Pages**:
  - `/login`: Form with email, password show/hide toggle, loading feedback, inline error validation.
  - `/register`: Form with full name, email, password strength checklist.
  - `/datasets`:
    - Responsive table listing datasets with format badges, dimensions, version badges, and updated dates.
    - Drag-and-drop & file picker upload dialog with real-time format/size pre-checks.
    - Upload progress bar and stage feedback (`Uploading` -> `Validating` -> `Success`).
    - Version history modal with per-version download actions.
- **Application Shell**:
  - `Header`: Authenticated user menu avatar, initials, name/email display, and logout dropdown.
  - `Sidebar`: Active links directly navigating to `/datasets` and `/`.
