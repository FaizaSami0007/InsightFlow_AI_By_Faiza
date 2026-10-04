# Test Strategy

## Unit

Test deterministic logic heavily:
- schema inference
- type normalization
- quality metrics
- analytical operations
- authorization
- dashboard schema validation

## Integration

- API + PostgreSQL
- dataset ingestion + storage
- DuckDB execution
- AI provider contract
- tool registry

## E2E

Primary journey:

```text
Sign in
→ Upload CSV
→ Process
→ Inspect quality
→ Ask question
→ Validate evidence
→ Generate chart
→ Save dashboard
→ Modify dashboard
```

## AI regression

Maintain a fixed benchmark dataset/questions. Store expected intent/tool/result properties rather than relying only on free-form text similarity.

## Security tests

Include:
- prompt injection
- cross-user dataset access
- SQL injection
- unsafe file upload
- rate-limit bypass
- sensitive output leakage

## Accessibility tests

- keyboard-only journey
- semantic landmark checks
- focus management
- chart alternative content
