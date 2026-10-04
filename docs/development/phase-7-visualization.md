# Phase 7 — Visualization Intelligence Architecture

## Overview
Phase 7 introduces a safe, context-aware visualization intelligence layer that evaluates validated deterministic analytical results (from Phase 4 DuckDB analytics) and recommends, validates, and renders institutional-grade interactive visualizations without arbitrary code execution.

---

## Architectural Principles

```
                 ANALYTICAL RESULT
                         │
                         ▼
                Visualization
                  Intelligence
                         │
             ┌───────────┴───────────┐
             ▼                       ▼
        Rule Engine             AI Recommendation
             │                       │
             └───────────┬───────────┘
                         ▼
                  Chart Validator
                         │
                         ▼
                Chart Specification
                         │
                         ▼
               Deterministic Renderer
                         │
                         ▼
                 Interactive Chart
```

1. **Analytical Truth Single Source**: The visualization pipeline NEVER computes analytical metrics, aggregates, or calculations. It strictly consumes validated results from `AnalysisJob`.
2. **Zero Code Execution**: The LLM NEVER generates JavaScript, React components, raw HTML, SVG scripts, or Python execution strings.
3. **Deterministic Safety Fallback**: If an AI recommendation or user request is invalid for the result schema, the system automatically falls back to the deterministic recommendation engine or a data table.
4. **End-to-End Provenance**: Every visualization specification binds directly to `analysis_id`, `dataset_id`, and `dataset_version_id`.
