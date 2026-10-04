# Phase 6: Multi-Turn Context Resolution & Dynamic Suggestions

## 1. Context Resolution Strategy

When a user engages in conversational analytics, each query is resolved within a structured multi-turn hierarchy:

1. **Dataset & Version Pinning**: Questions inherit the active `dataset_id` and `dataset_version_id`.
2. **Conversation History Window**: Recent turns are passed through `ContextBuilder.build_bounded_messages(history, max_turns=6)`, preserving previous tool arguments (e.g. `[Executed: group_by with args {'dimensions': ['region']}]`).
3. **Pronoun & Implicit Reference Resolution**: When the user asks `"What about profit?"` or `"Show the top 3"`, the orchestrator extracts the implicit dimension (`region`) and metric from previous turns.
4. **Clarification Continuations**: When an ambiguous term is clarified, the pending analytical intent is executed immediately with the chosen column.

---

## 2. Dynamic Suggestion Engine

To help users discover meaningful analytical questions, `ContextBuilder.generate_suggested_questions` dynamically evaluates:
- **Available Dimensions**: e.g., `region`, `category`, `customer_type`.
- **Available Measures**: e.g., `revenue`, `profit`, `quantity`.
- **Temporal Fields**: e.g., `order_date`, `created_at`.
- **Executed Tool Output**: Suggests ranking expansions, alternative breakdowns, correlations, and trend analyses.

### Validation Rule:
All suggested questions are strictly verified against actual columns in the dataset schema before being returned. Unsupported operations or nonexistent fields are never suggested.
