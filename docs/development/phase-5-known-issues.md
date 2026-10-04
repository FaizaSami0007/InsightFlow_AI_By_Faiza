# Phase 5: Known Issues & Limitations

## 1. Known Limitations

1. **Single Provider Active Per Session**:
   - Currently, one primary LLM provider (`GeminiProvider` or `MockLLMProvider`) is configured globally at startup via environment variables. Dynamic per-request multi-model routing is deferred to future releases.

2. **Synchronous Tool Calling Loop**:
   - Tool calls requested by the model are executed sequentially. Parallel independent tool execution within a single turn is planned for performance optimization in future iterations.

3. **In-Memory Mock State**:
   - `MockLLMProvider` heuristics cover standard golden test cases (group by, statistics, correlation, ambiguous categories, prompt injections). Arbitrary open-ended conversational questions fall back to default template responses when using the mock provider in test mode.
