# Phase 6: Conversational Security, User Isolation & Prompt Defense

## 1. Multi-Tenant Conversation & Dataset Isolation

1. **User-Scoped Conversations**:
   - `AIConversation` and `AIMessage` rows are strictly scoped by `user_id`.
   - Access to `/api/v1/ai/conversations/{id}` enforces SQL filtering on `user_id == current_user.id`. Cross-user access returns `404 Not Found`.
2. **Dataset Authorization at Query Time**:
   - Before executing any analytical turn in a conversation, `AIOrchestrator` verifies dataset ownership (`Dataset.owner_id == user.id`).
   - If a dataset is deleted or access is revoked, analytical turns fail immediately without disclosing schema or profile context to the LLM.

---

## 2. Multi-Turn Context Injection Defense

1. **Separation of Instructions & Context**:
   - Schema and quality alerts are isolated inside `<dataset_context>` delimiters.
   - Historical tool outputs are structured inside `<tool_result>` blocks.
   - The system prompt explicitly instructs the LLM that historical messages and dataset values are DATA, not executable instructions.
2. **Untrusted User Message Filtering**:
   - User messages attempting prompt injection (e.g., `"Ignore previous instructions"`, `"Override system prompt"`) are intercepted and neutralized.

---

## 3. Tool Allowlist & Parameter Enforcement

- The conversational layer can only invoke tools explicitly registered in the Phase 4 `AnalysisRegistry`.
- Direct SQL execution, arbitrary code evaluation (`eval`/`exec`), direct filesystem access, and external network requests are strictly blocked.
