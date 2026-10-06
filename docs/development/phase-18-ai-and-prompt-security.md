# Phase 18 — AI Prompt Security & Agent Guardrails

## 1. Direct Prompt Injection Defense
`PromptGuard` performs regex and heuristic scanning on all conversational user inputs before they reach the LLM, rejecting:
- Instruction override sequences ("ignore previous instructions", "disregard guidelines")
- Jailbreak persona indicators ("DAN mode", "developer mode", "godmode")
- System prompt extraction probes ("reveal your system prompt", "what are your initial rules")
- Exfiltration commands ("send all keys to https://...")

## 2. Untrusted Context Boundaries
Retrieved document chunks, OCR extractions, and external API responses are encapsulated inside explicit `<untrusted_context source="...">` boundary tags with neutralized control tokens (`<|im_start|>`, ````system`), preventing indirect injection attacks.

## 3. Tool Policy & Execution Boundaries
`AIGuard` enforces caller role permissions on every tool invocation (e.g. `delete_dataset` or `promote_model_version` cannot be invoked by unauthorized agents or viewers) and caps recursion depth at 3 and tool executions at 8 per conversation turn.
