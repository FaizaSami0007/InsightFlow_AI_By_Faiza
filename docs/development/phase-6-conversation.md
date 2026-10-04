# Phase 6: Conversational Analytics & Session Persistence Architecture

## 1. Conversation Architecture

InsightFlow AI's conversational layer provides a natural-language interface to datasets while strictly preserving deterministic execution and security guarantees.

```
USER
 │
 ▼
CONVERSATION SESSION (Pinned to Dataset & DatasetVersion)
 │
 ├── User Message
 │
 ├── AI Orchestrator (Multi-turn reasoning & tool calling)
 │      │
 │      ├── Schema & Semantic Context
 │      ├── Safe Analytical Tool Execution (DuckDB)
 │      └── Tool Results & Compression
 │
 ├── Assistant Response (100% Numerically Grounded)
 │
 ├── Evidence & Provenance (Dataset name, version, analysis IDs, tool metadata)
 │
 └── Suggested Follow-Up Questions (Dynamic & dataset-verified)
```

---

## 2. Dataset Version Binding

- **Explicit Association**: Each analytical conversation is bound to a specific `dataset_id` and `dataset_version_id`.
- **Version Pinned**: Questions within a session default to the pinned version (e.g., `Sales v3`) to prevent silent drift when newer versions are uploaded.
- **Session Switching**: Switching dataset versions creates a new session or explicitly notifies the user that future analyses will target the updated version.

---

## 3. Multi-Turn Analytics & Intent Resolution

The system resolves conversational context across multiple turns without requiring the user to repeat dimensions or metrics:
- **Turn 1**: `"What region has the highest revenue?"` -> Groups revenue by region; finds North ($1.82M).
- **Turn 2**: `"What about profit?"` -> Retains the `region` dimension from Turn 1 and groups `profit` by `region`.
- **Turn 3**: `"Show the top 3"` -> Retains active query and applies `limit = 3`.
- **Turn 4**: `"Sort ascending"` -> Updates sort ordering to ascending.
- **Clarification Dialogs**: If an ambiguous term (e.g. `category`) is used when multiple columns exist (`product_category`, `customer_category`), the system pauses, presents a clarification question, and upon user response seamlessly resumes the pending query.
