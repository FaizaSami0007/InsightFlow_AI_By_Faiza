# Phase 6: Known Issues & Limitations

## 1. Known Limitations

1. **Short-Term Context Window**:
   - Sliding window bounds conversation memory to `max_turns = 6` to preserve token budgets. Long conversations older than 6 turns omit earlier queries unless summarized.
2. **Sequential Multi-Turn Intent Execution**:
   - Multi-turn follow-ups are resolved step-by-step per request. Concurrent multi-clause compound inquiries (e.g., `"Show sales by region AND also show profit by category"`) execute the first identified clause in Phase 6. Compound multi-step queries will be enhanced in future phases.
3. **Frontend Markdown Formatting**:
   - Numerical formatting uses display-side typography. Exact underlying values remain unchanged in the DuckDB analytics registry.
