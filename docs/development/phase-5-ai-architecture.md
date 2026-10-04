# Phase 5: AI Orchestration & Structured Tool Calling Architecture

## 1. Architectural Overview

InsightFlow AI decouples the reasoning capabilities of Large Language Models (LLMs) from the computational execution of data analytics. The LLM acts exclusively as an **orchestration and synthesis agent**, while all statistical calculations, aggregations, filtering, and data transformations are executed by the deterministic analytical engine implemented in Phase 4.

```
+-------------------------------------------------------------------------+
|                                USER                                     |
+-------------------------------------------------------------------------+
                                    │
                                    ▼
+-------------------------------------------------------------------------+
|                       CONTEXT BUILDER & SANITIZER                       |
|   - Bounded schema, semantic roles, data quality, & prompt delimiters   |
+-------------------------------------------------------------------------+
                                    │
                                    ▼
+-------------------------------------------------------------------------+
|                          LLM PROVIDER LAYER                             |
|   - Google Gemini REST Adapter / Deterministic Mock Provider            |
+-------------------------------------------------------------------------+
                                    │
                                    ▼ (Structured Tool Call)
+-------------------------------------------------------------------------+
|                         AI TOOL ADAPTER & POLICY                        |
|   - Tool allowlist verification                                         |
|   - Parameter schema validation                                         |
|   - Semantic validation (dimensions vs measures)                        |
|   - Dataset ownership & isolation checks                                |
+-------------------------------------------------------------------------+
                                    │
                                    ▼
+-------------------------------------------------------------------------+
|                  PHASE 4 DETERMINISTIC ANALYTICS ENGINE                 |
|   - SafeSQLBuilder -> DuckDB In-Memory Execution                        |
+-------------------------------------------------------------------------+
                                    │
                                    ▼ (Validated Analytical Result)
+-------------------------------------------------------------------------+
|                         RESULT COMPRESSOR & LLM                         |
|   - Truncates to MAX_TOOL_RESULT_ROWS                                   |
|   - Synthesizes 100% numerically grounded answer with citations         |
+-------------------------------------------------------------------------+
                                    │
                                    ▼
+-------------------------------------------------------------------------+
|                                USER                                     |
+-------------------------------------------------------------------------+
```

---

## 2. Core Architectural Principles

1. **Analytical Engine as the Single Source of Truth**: The LLM is never allowed to calculate sums, averages, counts, or correlations in its head. All numerical metrics must originate from executed tools.
2. **Zero Direct Database Access**: The AI Provider layer has zero direct connection to PostgreSQL, DuckDB, or underlying file storage.
3. **Structured Tool Calling**: Tools are invoked via strictly typed specifications (`ToolCallSpec`) validated against JSON Schema definitions.
4. **Data Isolation & Injection Defense**: Dataset column names, cell values, and tool results are explicitly tagged within `<dataset_context>` and `<tool_result>` blocks, treated strictly as untrusted data.
5. **Loop and Cost Controls**: Orchestration loops are capped (`MAX_TOOL_CALLS_PER_REQUEST = 5`), and results are compressed (`MAX_TOOL_RESULT_ROWS = 20`) to prevent context blowup and infinite recursion.
