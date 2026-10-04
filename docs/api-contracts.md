# API Contract Conventions

## Versioning

All public endpoints live under `/api/v1`.

## Success

Return predictable JSON objects with stable field names.

## Error model

```json
{
  "error": {
    "code": "DATASET_NOT_READY",
    "message": "The dataset is still processing.",
    "request_id": "...",
    "details": {}
  }
}
```

Never expose stack traces, SQL, secrets, or provider internals in production responses.

## Idempotency

Upload and mutation endpoints that can be retried should support idempotency where duplicate effects would be harmful.
