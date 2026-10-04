# Phase 5: Structured Tool Calling & Registry Integration

## 1. Tool Adapter

`AIToolAdapter` (`app.ai.tools.adapter`) bridges the Phase 4 deterministic analytical tools (`AnalysisRegistry`) with the LLM layer.

### Registered Tools Exposed to AI
- **`descriptive_stats`**: Summary statistics (min, max, mean, stddev, percentiles, null count) across numeric and categorical columns.
- **`group_by`**: Aggregations (`SUM`, `AVG`, `COUNT`, `MIN`, `MAX`) grouped across dimensions with sorting and limit clauses.
- **`correlation`**: Pearson correlation matrix for numerical measures.
- **`time_series_agg`**: Temporal binning (`day`, `week`, `month`, `year`) and aggregation over time-based columns.
- **`filter`**: Structured predicate filtering (`eq`, `neq`, `gt`, `gte`, `lt`, `lte`, `in`, `is_null`, `is_not_null`, `between`).

---

## 2. Tool Definition Mapping

Each Phase 4 tool is dynamically mapped to a `ToolDefinition` with clean JSON Schema parameter declarations derived from `AnalysisToolMetadata`.

```json
{
  "name": "group_by",
  "description": "Groups records by dimensions and computes aggregations (SUM, AVG, COUNT, MIN, MAX).",
  "parameters": {
    "type": "object",
    "properties": {
      "dimensions": { "type": "array", "items": { "type": "string" } },
      "aggregations": {
        "type": "array",
        "items": {
          "type": "object",
          "properties": {
            "column": { "type": "string" },
            "agg_type": { "type": "string", "enum": ["SUM", "AVG", "COUNT", "MIN", "MAX"] },
            "alias": { "type": "string" }
          },
          "required": ["column", "agg_type"]
        }
      },
      "sort_by": {
        "type": "array",
        "items": {
          "type": "object",
          "properties": {
            "column": { "type": "string" },
            "order": { "type": "string", "enum": ["ASC", "DESC"] }
          }
        }
      },
      "limit": { "type": "integer" }
    },
    "required": ["dimensions"]
  }
}
```

---

## 3. Tool Execution & Validation Pipeline

Before any tool is executed:
1. **Tool Allowlist Check**: Rejects any tool name not present in `AnalysisRegistry`.
2. **Schema & Argument Validation**: Validates that required parameters are provided and structured correctly.
3. **Dataset Lineage & Authorization**: Validates that the requesting user owns the dataset and that the target version is loaded in DuckDB.
4. **Deterministic Safe Execution**: Executes via `AnalyticsService.run_analysis`, which executes parametrized, injection-safe DuckDB queries.
