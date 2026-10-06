# Phase 16 — Feature Contracts & Output Validation

## 1. Feature Contract Specification
Feature contracts are immutable JSON schema specifications stored on `MLModelVersion.feature_schema`.

### Features Schema Attributes
- `data_type`: `"numeric"`, `"categorical"`, `"datetime"`, `"boolean"`, `"text"`.
- `is_required`: Boolean flag enforcing feature presence.
- `min_value` / `max_value`: Value range bounds for numeric features.
- `allowed_categories`: Strict whitelist for categorical features.
- `nullable`: Whether null/None is permitted.

## 2. Output Validation
`OutputValidator` enforces:
- Non-finite rejection (`NaN`, `Inf`, `-Inf` trigger validation failure).
- Non-negativity bounds when `allow_negative=False`.
- Upper and lower prediction bounds.
