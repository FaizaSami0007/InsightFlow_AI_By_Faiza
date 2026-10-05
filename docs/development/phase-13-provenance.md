# Phase 13 — Scenario Provenance & Immutability

## 1. Provenance Schema
Every simulation stamps complete lineage tracking:
```json
{
  "scenario_id": "8f3b201a-...",
  "dataset_id": "4b7a5731-...",
  "dataset_version_id": "1ce78634-...",
  "baseline_source": "HISTORICAL_AGGREGATE",
  "engine_version": "scenario_engine_v1",
  "is_simulation": true,
  "isolation_context": "read_only_in_memory_view"
}
```

## 2. Source Data Immutability
- All calculations occur in read-only DuckDB in-memory views.
- No `UPDATE`, `INSERT`, or `DELETE` statements are ever executed against underlying dataset files or production storage tables.
- Scenarios are saved as immutable historical records. If assumptions are modified, a new scenario execution ID is generated.
