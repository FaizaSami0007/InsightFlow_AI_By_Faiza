# Phase 15: Known Issues & Technical Limitations

## 1. Known Technical Considerations
1. **Dynamic LLM Decomposition Latency**:
   - For ultra-complex 5+ node DAGs, sequential dispatch of interdependent LLM prompts can add 1.5–3 seconds of latency. Parallel batching with `asyncio.gather` mitigates this for independent nodes.
2. **Context Window Scaling on Wide DAGs**:
   - Synthesizing results across 5+ specialized agents requires compact summaries in `EvidenceItem` models to stay well within model context limits.
3. **Database Concurrency on Task Logging**:
   - Async session logging for concurrent tasks requires careful transaction demarcation when storing task statuses in `ai_tasks`.

## 2. Planned Enhancements (Phase 16)
- Streaming multi-agent tokens via SSE / WebSocket directly to the frontend DAG graph in real time.
- Dynamic subagent tool synthesis based on runtime semantic layer changes.
