# AI Provider Contract

## Goal

The application must be able to switch model providers without changing business logic.

## Interface

```text
LLMProvider
├── structured_generate()
├── stream_generate()
├── embed()              # optional; not required for MVP
└── health()
```

## Provider selection

Environment configuration selects the provider. The default development provider is intentionally configurable rather than hard-coded.

## Required model capabilities

- Structured output / JSON schema
- Tool calling or equivalent structured planning
- Streaming for conversational UX
- Reasonable context window

## Model routing

Do not implement multi-model routing until cost/latency evaluation proves it is useful. Keep the interface ready for it.
