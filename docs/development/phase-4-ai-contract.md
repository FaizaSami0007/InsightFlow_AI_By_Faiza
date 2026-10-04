# Phase 4 to Phase 5 AI Tool-Calling Contract

This specification outlines how future AI agents and LLM orchestrators (introduced in Phase 5) will interface with the deterministic analytics engine.

---

## 1. Tool Discovery Interface
Future AI components will discover available analytical capabilities dynamically via:
`GET /api/v1/analytics/tools`

Each tool provides:
- `name`: Machine identifier (e.g. `group_by`, `correlation`, `distribution`).
- `description`: Detailed explanation of when to call the tool.
- `input_schema`: Standard JSON Schema declaring required and optional parameters.
- `semantic_prerequisites`: Constraints specifying required column roles (`MEASURE`, `DIMENSION`, `DATE`).

---

## 2. Execution Contract
AI agents will emit a structured JSON analysis request:
```json
{
  "dataset_id": "<uuid>",
  "dataset_version_id": "<uuid>",
  "operation": "group_by",
  "parameters": {
    "dimensions": ["region"],
    "aggregations": [
      {"column": "revenue", "agg_type": "SUM", "alias": "total_revenue"}
    ]
  },
  "filters": {
    "column": "order_date",
    "operator": ">=",
    "value": "2026-01-01"
  }
}
```

The deterministic analytics engine executes the request, verifies mathematical accuracy, records provenance, and returns:
```json
{
  "analysis_id": "<uuid>",
  "status": "COMPLETED",
  "operation": "group_by",
  "columns": ["region", "total_revenue"],
  "rows": [
    {"region": "North", "total_revenue": 1820000.0}
  ],
  "provenance": {
    "dataset_version_id": "<uuid>",
    "execution_time_ms": 14.2
  }
}
```

The future AI agent reasons *about* these returned numbers, but never calculates them independently.
