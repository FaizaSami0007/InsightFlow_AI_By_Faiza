# Phase 6: Conversational Testing Strategy & Test Suites

## 1. Testing Strategy

All Phase 6 tests are architected to run **100% offline** without requiring external cloud accounts or live vendor API keys.

---

## 2. Test Suite Structure

1. **`tests/test_conversations_api.py`**:
   - `test_conversation_lifecycle_and_starters`: Tests session creation, dynamic starters retrieval, conversation listing, detail fetching, and deletion.
   - `test_conversation_user_isolation`: Verifies that User B cannot read or delete User A's private conversations (returns 404).

2. **`tests/test_multi_turn_analytics.py`**:
   - `test_multi_turn_flow_and_follow_up_questions`: Verifies Turn 1 (initial group by), Turn 2 (implicit dimension follow-up on profit), Turn 3 (limit modification to 3), and Turn 4 (sort direction modification to ASC).
   - `test_ambiguity_clarification_flow`: Verifies that ambiguous category questions trigger clarification questions (`needs_clarification=True`), and user column answers resume the analytical plan without session reset.
   - `test_unsupported_request_handling`: Verifies that unsupported forecasting/dashboard requests return honest capability disclaimers.

3. **`tests/test_phase6_evaluation.py`**:
   - 80+ deterministic evaluation test cases:
     - 10 simple analytical queries
     - 10 aggregation queries
     - 10 grouping queries
     - 10 filtering and correlation queries
     - 10 unsupported capability requests
     - 10 prompt injection & security defense queries
