# Phase 19 — RAG & AI Orchestration Optimization

## 1. Context Truncation & Token Budgeting
- RAG retrieval limits top-k document chunks to the most relevant semantic matches (default k=4).
- Conversational history truncates oldest turns past token threshold (4,000 tokens) while preserving system instructions and numerical facts.

## 2. Multi-Agent Resource Budgets
- Enforced hard limits:
  - Max 8 tool invocations per turn
  - Max recursion depth 3
  - Max 5 parallel subtasks
- Circuit breaker stops runaway loops and logs warning alerts via `AlertManager`.
