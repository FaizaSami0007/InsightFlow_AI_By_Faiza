# Data Governance

## Data lifecycle

```text
Upload → Validate → Process → Ready → Archive → Delete
```

## Required controls

- File type allowlist
- Maximum file size
- Maximum row/column limits
- Malware scanning integration point
- PII detection
- Sensitive-column masking
- Retention policy
- User-initiated deletion
- Dataset export
- Dataset version history

## PII policy

Detected PII should be classified and masked in AI context by default. The application UI may show classification status to authorized users without exposing raw sensitive values unnecessarily.

## Deletion

Deletion must cover:
- metadata
- object/file storage
- analytical copies
- derived artifacts
- caches
- search indexes when introduced

Deletion jobs must be observable and retryable.

## Tenant isolation

Every dataset access path must carry an authorization scope. Never rely solely on frontend filtering.
