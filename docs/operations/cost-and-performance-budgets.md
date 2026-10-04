# Cost & Performance Budgets

## AI

Set per-request limits for:
- input tokens
- output tokens
- tool calls
- retries
- wall-clock time

## Analytics

Set:
- maximum file size
- maximum rows/columns for synchronous operations
- query timeout
- result row limit

## UX

Prefer progressive loading. Never block the whole application while a large dataset processes.

## Principle

Budgets are guardrails, not performance claims. Measure actual behavior and revise based on evidence.
