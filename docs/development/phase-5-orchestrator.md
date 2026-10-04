# Phase 5: AI Orchestrator

## 1. Orchestrator Overview

`AIOrchestrator` (`app.ai.orchestrator.orchestrator`) manages the lifecycle of AI-driven analytical sessions. It acts as the bridge between user intent, context construction, LLM reasoning, deterministic tool execution, and session persistence.

```
Incoming Request
      │
      ▼
Verify Dataset Ownership & Retrieve Lineage
      │
      ▼
ContextBuilder: Build Schema, Semantic Layer & Quality Context
      │
      ▼
Assemble Bounded Conversation History (Max Window)
      │
      ▼
Loop (Max 5 tool iterations):
  ├── Invoke LLMProvider.generate()
  ├── If finish_reason == 'stop' -> Exit Loop
  └── If finish_reason == 'tool_calls':
        ├── Validate Tool Name against Allowlist
        ├── Validate Parameters against Tool Schema
        ├── Authorize Dataset & Execute via AnalyticsService
        ├── Record Analysis Provenance ID
        ├── Compress Tool Result (Max 20 rows)
        └── Append ToolResultSpec to Working Messages
      │
      ▼
Persist AIMessage & Update Conversation
      │
      ▼
Record AIRequestLog (Latency, Token Usage, Tool Count, Status)
      │
      ▼
Return AIChatResponse to Client
```

---

## 2. Loop Protection & Resource Limits

To prevent infinite recursion, excessive costs, and context exhaustion:
- **`MAX_TOOL_CALLS_PER_REQUEST = 5`**: Hard limit on consecutive tool executions per user prompt.
- **`MAX_TOOL_RESULT_ROWS = 20`**: Tool results containing large datasets are summarized (row count, summary statistics, top preview rows).
- **`MAX_HISTORY_TURNS = 10`**: Sliding window of past messages sent to the model to avoid context window explosion.

---

## 3. Provenance & Citations

Whenever an analytical tool executes, the resulting `analysis_id` is linked to the message and returned in `AIChatResponse.citations` (e.g. `Based on Sales v3 — Analysis #A-102: group_by`). This ensures end-to-end explainability and auditability.
