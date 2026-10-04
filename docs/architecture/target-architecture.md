# Target Architecture

```text
                        ┌───────────────────────┐
                        │       Next.js Web      │
                        │  UX + Dashboard UI     │
                        └───────────┬───────────┘
                                    │ HTTPS/JSON
                        ┌───────────▼───────────┐
                        │       FastAPI API      │
                        │ auth / datasets / AI  │
                        └───────┬───────┬───────┘
                                │       │
                  ┌─────────────┘       └──────────────┐
                  ▼                                    ▼
        ┌──────────────────┐                 ┌──────────────────┐
        │ PostgreSQL       │                 │ AI Orchestrator  │
        │ app state        │                 │ plan + tools     │
        └──────────────────┘                 └────────┬─────────┘
                                                       │
                                                ┌──────▼──────┐
                                                │ Tool Policy │
                                                └──────┬──────┘
                                                       │
                                      ┌────────────────▼──────────────┐
                                      │ DuckDB + Polars Analytics     │
                                      └────────────────┬──────────────┘
                                                       │
                                                ┌──────▼──────┐
                                                │ Provenance  │
                                                └─────────────┘
```

## Architectural invariants

1. Frontend never owns authoritative analytics.
2. LLM output is untrusted input.
3. Tool execution is allowlisted.
4. Dataset access is authorization-scoped.
5. Analytical operations are deterministic and reproducible.
6. Dashboard JSON is validated before rendering.
7. Every AI action is observable.
8. Every important analysis has provenance.

## Modular monolith boundary

Modules remain independently testable while sharing one deployable backend until scale proves a service boundary is necessary.
