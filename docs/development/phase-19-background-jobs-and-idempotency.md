# Phase 19 — Background Jobs & Idempotent Execution

## 1. Idempotent Sync & Ingestion Jobs
Background connector synchronizations and ingestion tasks use idempotent keys (`sync_job_id`, `version_id`) ensuring network retries never produce duplicate dataset versions or corrupted records.

## 2. Bounded Exponential Backoff
- Failed background jobs retry with exponential backoff (e.g. 1s, 2s, 4s) up to 3 attempts.
- Non-retryable errors (invalid credentials, permission denied, schema mismatch) fail immediately without wasteful retries.
