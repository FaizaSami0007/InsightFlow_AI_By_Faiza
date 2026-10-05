# Phase 12: Proactive Insight Intelligence & Lifecycle Engine

## 1. Insight Model

Proactive Insights represent structured, explainable analytical findings generated alongside anomaly detection:
- `insight_id`: Unique UUID identifier.
- `insight_type`: `ANOMALY`, `TREND_CHANGE`, `FORECAST_DEVIATION`, `CONTRIBUTION`, `DATA_QUALITY`.
- `title`: Concise human-readable finding (e.g. `"Revenue in West fell 27% below baseline"`).
- `summary`: Detailed mathematical narrative without fabricated details.
- `severity`: Deterministic classification (`CRITICAL`, `HIGH`, `MEDIUM`, `LOW`, `INFO`).
- `dedup_key`: Deterministic hashing key (`{dataset_id}:{metric}:{period}:{subgroup}`) to prevent repeated redundant alerts.
- `status`: Lifecycle state (`DETECTED`, `ACKNOWLEDGED`, `DISMISSED`, `RESOLVED`).

## 2. User Lifecycle & Feedback

Users can acknowledge, resolve, or dismiss insights. User feedback (`useful`, `not_useful`, `expected_behavior`) is recorded for platform telemetry without autonomous model corruption.
