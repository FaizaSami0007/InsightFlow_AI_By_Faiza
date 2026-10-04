# Data Lineage & Analytical Provenance

## Requirement

Every answer and visualization generated from data must be traceable back to the exact dataset version and analytical operation.

## Provenance record

```json
{
  "dataset_id": "...",
  "dataset_version_id": "...",
  "schema_hash": "...",
  "analysis_id": "...",
  "tool_name": "group_by",
  "tool_version": "1.0",
  "input": {"dimension":"region","measure":"revenue","aggregation":"sum"},
  "filters": [],
  "result_hash": "...",
  "created_at": "..."
}
```

## Why it matters

- Reproducibility
- Debugging
- Auditability
- User trust
- AI evaluation
- Dashboard refresh correctness

## Rule

A generated insight without provenance is not considered a trusted insight.
