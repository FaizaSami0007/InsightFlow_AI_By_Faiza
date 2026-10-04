# Phase 5: Testing Strategy & Offline CI Verification

## 1. Testing Strategy

All Phase 5 AI tests are designed to execute **100% offline** without requiring external internet access, API keys, or cloud provider accounts.

---

## 2. Test Suites

1. **`tests/test_ai_provider.py`**:
   - `MockLLMProvider` scripted response queues.
   - `MockLLMProvider` heuristic rule synthesis.
   - `GeminiProvider` payload serialization and schema conversion.
   - Provider factory fallback to mock when `LLM_API_KEY` is not provided.

2. **`tests/test_context_builder.py`**:
   - Schema context formatting.
   - Semantic layer role mapping.
   - Data quality warning summarization.
   - Tool result compression (`MAX_TOOL_RESULT_ROWS = 20`).
   - Conversation history window bounding (`MAX_HISTORY_TURNS = 10`).

3. **`tests/test_ai_security.py`**:
   - Prompt injection defense test cases.
   - Tool allowlist verification and unknown tool rejection.
   - Multi-tenant dataset isolation (prevent cross-user dataset access).

4. **`tests/test_ai_api.py`**:
   - Conversation lifecycle endpoints (`POST /api/v1/ai/conversations`, `GET`, `DELETE`).
   - Message persistence and retrieval.

5. **`tests/test_ai_orchestrator.py`**:
   - Multi-turn tool calling and numerical grounding.
   - Orchestration loop limit enforcement (`MAX_TOOL_CALLS_PER_REQUEST`).
   - Ambiguity clarification flow.
