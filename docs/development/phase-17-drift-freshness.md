# Phase 17 — Schema Drift & Freshness Evaluation Engines

## 1. Schema Drift Engine (`ConnectorDriftEngine`)
Located in `apps/api/app/connectors/drift_engine.py`.

The Drift Engine detects schema mutations between successive sync cycles:
- **Added Columns:** Flags new fields discovered in upstream sources (Severity: `WARNING`).
- **Removed Columns:** Flags missing fields that may impact downstream analytical models and dashboards (Severity: `CRITICAL`).
- **Type Shifts:** Flags datatype alterations (e.g. `INTEGER` to `VARCHAR`, `FLOAT` to `JSON`) (Severity: `CRITICAL`).
- **Actionable Recommendations:** Generates clear remediation steps for data engineers.

## 2. Freshness Engine (`FreshnessEngine`)
Located in `apps/api/app/connectors/drift_engine.py`.

Evaluates connection freshness against configured SLA intervals:
- `FRESH`: Ingestion executed within the expected schedule window (Score: 80.0–100.0).
- `STALE`: Sync is overdue by up to 1.5x of the scheduled interval (Score: 50.0–75.0).
- `OVERDUE`: Sync is critically overdue, indicating stalled upstream pipelines (Score: 10.0–40.0).
